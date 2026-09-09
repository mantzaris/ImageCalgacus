"""GPU PixelCNN++ and lossless observable-pixel I/O."""
import hashlib
import importlib.metadata
from pathlib import Path
import struct
import time
import numpy as np
from PIL import Image

from .pixel_probabilities import RGBConditionals
from .runtime import configure_gpu, verified_model, allocation_snapshot


def read_png(path, shape=(31, 32, 3)):
    data = Path(path).read_bytes()
    if len(data) > 2 * 1024 * 1024 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("invalid PNG signature/size")
    if len(data) < 33 or data[12:16] != b"IHDR":
        raise ValueError("missing PNG header")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", data[16:29])
    if (height, width, 3) != shape or (depth, color, compression, filtering) != (8, 2, 0, 0):
        raise ValueError("PNG must be exact dimensions, 8-bit truecolor")
    offset = 8
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        offset += 12 + length
        if offset > len(data):
            raise ValueError("truncated PNG chunk")
        if kind == b"IEND":
            if length != 0 or offset != len(data):
                raise ValueError("trailing PNG data")
            break
    else:
        raise ValueError("missing PNG end")
    with Image.open(path) as check:
        check.verify()
    with Image.open(path) as image:
        if image.mode != "RGB" or image.size != (width, height):
            raise ValueError("PNG mode changed")
        pixels = np.asarray(image, dtype=np.uint8).copy()
    if pixels.shape != shape:
        raise ValueError("wrong pixel shape")
    return pixels


def write_png(path, pixels):
    pixels = np.asarray(pixels)
    if pixels.dtype != np.uint8 or pixels.ndim != 3 or pixels.shape[2] != 3:
        raise ValueError("RGB uint8 required")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path, format="PNG", compress_level=6)
    if not np.array_equal(read_png(path, pixels.shape), pixels):
        raise ValueError("PNG roundtrip changed pixels")


class DistributionDigest:
    """Output-only exact stream fingerprints; no packet or diagnostic inputs."""
    def __init__(self):
        self.steps = 0
        self.hashes = {name: hashlib.sha256() for name in ("eligible_ids", "probabilities", "rank_order")}

    def observe(self, ids, probabilities, order):
        for name, values, dtype in (("eligible_ids", ids, "<i8"),
                                    ("probabilities", probabilities, "<f8"),
                                    ("rank_order", order, "<i8")):
            values = np.asarray(values, dtype=dtype)
            self.hashes[name].update(struct.pack("<QQ", self.steps, values.size))
            self.hashes[name].update(values.tobytes(order="C"))
        self.steps += 1

    def summary(self):
        return {"steps": self.steps, "format": "position,length:uint64le; ids/order:int64le; probabilities:float64le",
                **{name+"_sha256": value.hexdigest() for name, value in self.hashes.items()}}


class ImageBackend:
    def __init__(self, profile, execution_mode="reference", audit=False):
        if execution_mode not in {"reference", "cuda_graph"}:
            raise ValueError("unknown image execution mode; no fallback")
        self.execution_mode = execution_mode
        self.audit = audit
        self.evidence = {"device": configure_gpu(profile, "image")}
        path = verified_model(profile, "image")
        import torch
        from .pixelcnn.model import PixelCNN
        self.torch = torch
        if importlib.metadata.version("torch") != "2.5.1+cu124":
            raise RuntimeError("unpinned PyTorch CUDA build")
        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise RuntimeError("selected CUDA device unavailable; CPU fallback forbidden")
        torch.set_num_threads(8)
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cuda.matmul.allow_tf32 = False
        self.device = torch.device("cuda:0")  # UUID mapping verified before import.
        started = time.monotonic()
        item = profile["image"]
        state = torch.load(path, map_location="cpu", weights_only=True)
        # Author checkpoint was saved from DataParallel. This is a bijective
        # namespace removal, followed by strict matching of every tensor.
        if not state or not all(key.startswith("module.") for key in state):
            raise ValueError("unexpected checkpoint key namespace")
        state = {key[len("module."):]: value for key, value in state.items()}
        self.model = PixelCNN(nr_resnet=item["nr_resnet"], nr_filters=item["nr_filters"],
                              nr_logistic_mix=item["nr_logistic_mix"], input_channels=3)
        mismatch = self.model.load_state_dict(state, strict=True)
        del state
        self.model.to(self.device)
        self.model.eval()
        torch.cuda.synchronize()
        self.load_seconds = time.monotonic() - started
        devices = sorted({str(p.device) for p in self.model.parameters()})
        if devices != ["cuda:0"] or any(b.device != self.device for b in self.model.buffers()):
            raise RuntimeError("image parameter/buffer not on selected CUDA device")
        self.evidence.update({"backend": "torch", "version": importlib.metadata.version("torch"),
                              "cuda_runtime": torch.version.cuda, "cudnn": torch.backends.cudnn.version(),
                              "model_sha256": item["model_sha256"], "strict_loading": True, "checkpoint_key_mapping": "strip uniform module. prefix",
                              "missing_keys": mismatch.missing_keys, "unexpected_keys": mismatch.unexpected_keys,
                              "parameter_devices": devices, "eval_mode": not self.model.training,
                              "deterministic_algorithms": True, "tf32": False,
                              "gpu_allocation": allocation_snapshot()})
        if not self.evidence["gpu_allocation"]:
            raise RuntimeError("image GPU allocation not observed")
        self.calls = 0
        self.cuda_milliseconds = 0.0
        self.canvas = np.zeros((32, 32, 3), dtype=np.uint8)
        self.position = 0
        self.conditionals = None
        self.digest = DistributionDigest() if audit else None
        self.execution_setup_seconds = 0.0
        self.evidence["execution_mode"] = execution_mode
        if execution_mode == "cuda_graph":
            self._prepare_graph()
        self.evidence["execution_setup_seconds"] = self.execution_setup_seconds

    def _prepare_graph(self):
        """Capture the unchanged model, with fixed addresses and side-stream warmup.
        No precision, launch-blocking, cuDNN or cuBLAS setting is relaxed.
        See PyTorch CUDA semantics and installed torch 2.5.1 cuda/graphs.py.
        """
        torch = self.torch
        started = time.monotonic()
        stream = torch.cuda.Stream()
        with torch.inference_mode():
            self.graph_input = torch.zeros((1, 3, 32, 32), device=self.device, dtype=torch.float32)
            stream.wait_stream(torch.cuda.current_stream())
            with torch.cuda.stream(stream):
                for _ in range(3):
                    warm_output = self.model(self.graph_input, sample=True)
            torch.cuda.current_stream().wait_stream(stream)
            torch.cuda.synchronize()
            del warm_output
            self.graph = torch.cuda.CUDAGraph()
            with torch.cuda.graph(self.graph, stream=stream):
                self.graph_output = self.model(self.graph_input, sample=True)
        torch.cuda.synchronize()
        self.graph_start = torch.cuda.Event(enable_timing=True)
        self.graph_end = torch.cuda.Event(enable_timing=True)
        self.execution_setup_seconds = time.monotonic() - started
        self.evidence.update(graph_warmup_forwards=3, graph_capture=True,
                             graph_capture_error_mode="global", graph_input_shape=[1, 3, 32, 32])

    def _graph_forward(self, canvas=None):
        torch = self.torch
        data = self.canvas if canvas is None else canvas
        # Exactly the reference's host float32 normalization and layout.
        normalized = (data.astype(np.float32) * np.float32(2 / 255) - np.float32(1))
        host = torch.from_numpy(normalized.transpose(2, 0, 1).copy()).unsqueeze(0)
        with torch.inference_mode():
            self.graph_input.copy_(host)
            self.graph_start.record()
            self.graph.replay()
            self.graph_end.record()
            torch.cuda.synchronize()
            self.cuda_milliseconds += self.graph_start.elapsed_time(self.graph_end)
            self.evidence["inference_mode"] = torch.is_inference_mode_enabled()
        self.calls += 1
        self.evidence.update(input_device=str(self.graph_input.device),
                             output_device=str(self.graph_output.device),
                             cuda_model_milliseconds=self.cuda_milliseconds)
        # Borrowed until the next forward. distribution() immediately copies the
        # selected parameters to CPU; no output from another sequence is reused.
        return self.graph_output

    def forward(self, canvas=None):
        if self.execution_mode == "cuda_graph":
            return self._graph_forward(canvas)
        torch = self.torch
        data = self.canvas if canvas is None else canvas
        normalized = (data.astype(np.float32) * np.float32(2 / 255) - np.float32(1))
        tensor = torch.from_numpy(normalized.transpose(2, 0, 1).copy()).unsqueeze(0).to(self.device)
        if tensor.device != self.device:
            raise RuntimeError("input not on selected CUDA device")
        start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        with torch.inference_mode():
            start.record()
            output = self.model(tensor, sample=True)
            end.record()
            torch.cuda.synchronize()
            self.cuda_milliseconds += start.elapsed_time(end)
            self.evidence["inference_mode"] = torch.is_inference_mode_enabled()
        self.calls += 1
        self.evidence["input_device"] = str(tensor.device)
        self.evidence["output_device"] = str(output.device)
        self.evidence["cuda_model_milliseconds"] = self.cuda_milliseconds
        return output

    def start(self, context):
        self.canvas.fill(0)
        if context is None:  # ordinary full-canvas feasibility only
            self.position = 0
        else:
            if len(context) != 96:
                raise ValueError("shared row must be exactly 96 bytes")
            self.canvas[0] = np.frombuffer(context, dtype=np.uint8).reshape(32, 3)
            self.position = 96
        self.conditionals = None
        if self.audit:
            self.digest = DistributionDigest()

    def distribution(self):
        if self.position >= 3072:
            raise ValueError("pixel capacity exhausted")
        if self.position % 3 == 0:
            pixel = self.position // 3
            output = self.forward()
            params = output[0, :, pixel // 32, pixel % 32].detach().cpu().numpy().astype(np.float64)
            del output
            self.conditionals = RGBConditionals(params)
        result = self.conditionals.distribution()
        if self.digest is not None:
            self.digest.observe(*result)
            self.evidence["distribution_digest"] = self.digest.summary()
        return result

    def observe(self, symbol):
        self.conditionals.observe(int(symbol))
        self.canvas.reshape(-1)[self.position] = symbol
        self.position += 1

    def probe(self):
        torch = self.torch
        self.start(None)
        with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,
                                               torch.profiler.ProfilerActivity.CUDA]) as prof:
            output = self.forward()
        kernels = [event for event in prof.events() if str(event.device_type).endswith("CUDA")]
        if not kernels:
            raise RuntimeError("no CUDA operator execution observed")
        self.evidence["cuda_kernel_count"] = len(kernels)
        self.evidence["cuda_kernel_examples"] = sorted({event.name for event in kernels})[:8]
        base = output[0, :, 1, 1].detach().cpu().numpy().copy()
        altered = self.canvas.copy()
        altered.reshape(-1)[(1 * 32 + 1) * 3:] = 255
        changed = self.forward(altered)[0, :, 1, 1].detach().cpu().numpy()
        if not np.array_equal(base, changed):
            raise ValueError("current/future pixels change current network parameters")
        self.evidence["causal_current_future_max_abs_difference"] = float(np.max(np.abs(base - changed)))
        # A second identical input checks deterministic GPU forward execution.
        repeated = self.forward()[0, :, 1, 1].detach().cpu().numpy()
        if not np.array_equal(base, repeated):
            raise ValueError("GPU pixel inference is nondeterministic")
        self.evidence["repeat_forward_equal"] = True
        return self.evidence

    def close(self):
        self.evidence["peak_cuda_allocated_bytes"] = self.torch.cuda.max_memory_allocated()
        self.evidence["peak_cuda_reserved_bytes"] = self.torch.cuda.max_memory_reserved()
        if self.execution_mode == "cuda_graph":
            self.graph.reset()
            del self.graph_output, self.graph_input, self.graph
        del self.model
        self.torch.cuda.empty_cache()
