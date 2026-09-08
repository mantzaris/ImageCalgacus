"""GPU llama.cpp adapter. RankCloak MIT adaptations; see THIRD_PARTY.md."""
import ctypes
import importlib.metadata
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import numpy as np

from .fixed_rank import stable_order, normalized
from .runtime import configure_gpu, verified_model, allocation_snapshot, sha256_file


def preload_pip_cuda_libraries():
    import nvidia
    loaded = []
    for root in nvidia.__path__:
        for relative in ("cuda_runtime/lib/libcudart.so.12", "cublas/lib/libcublasLt.so.12", "cublas/lib/libcublas.so.12"):
            path = Path(root) / relative
            if path.is_file():
                ctypes.CDLL(str(path), mode=ctypes.RTLD_GLOBAL)
                loaded.append(str(path))
    return loaded


def reset_model(model):
    model.reset()
    clear = getattr(model._ctx, "kv_cache_clear", None)
    if not callable(clear):
        raise RuntimeError("actual KV clear API unavailable; no silent reset approximation")
    clear()


def evaluate_context(model, ids):
    if not ids:
        raise ValueError("empty context")
    reset_model(model)
    model.eval(list(ids))


def tokenize_bytes(model, data):
    return list(model.tokenize(data, add_bos=False, special=False))


def detokenize_bytes(model, ids):
    value = model.detokenize(list(ids), special=False)
    if not isinstance(value, bytes):
        raise TypeError("exact byte detokenization required")
    return value


def consistent_candidate(model, prefix, token):
    raw = detokenize_bytes(model, prefix + [int(token)])
    try:
        raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False
    return tokenize_bytes(model, raw) == prefix + [int(token)]


class TextBackend:
    def __init__(self, profile):
        self.profile = profile
        self.evidence = {"device": configure_gpu(profile, "text")}
        path = verified_model(profile, "text")
        loaded = preload_pip_cuda_libraries()
        import llama_cpp
        from llama_cpp import Llama
        api = llama_cpp.llama_cpp
        if not api.llama_supports_gpu_offload():
            raise RuntimeError("llama.cpp has no GPU offload support; CPU fallback forbidden")
        library = Path(llama_cpp.__file__).parent / "lib/libggml-cuda.so"
        binary = library.read_bytes()
        controls = ["GGML_CUDA_DISABLE_GRAPHS", "GGML_CUDA_DISABLE_FUSION", "GGML_CUDA_FORCE_CUBLAS_COMPUTE_32F"]
        if any(flag.encode() not in binary for flag in controls):
            raise RuntimeError("backend does not expose approved CUDA replay controls")
        self.evidence.update({"backend": "llama-cpp-python", "version": importlib.metadata.version("llama-cpp-python"),
                              "cuda_library_sha256": sha256_file(library),
                              "loaded_cuda_libraries": loaded, "gpu_offload_supported": True,
                              "system_info": api.llama_print_system_info().decode(),
                              "model_sha256": profile["text"]["model_sha256"]})
        if "CUDA" not in self.evidence["system_info"]:
            raise RuntimeError("CUDA backend absent from system information")
        if self.evidence["version"] != "0.3.23":
            raise RuntimeError("unpinned llama-cpp-python version")
        started = time.monotonic()
        saved_stderr = os.dup(2)
        with tempfile.TemporaryFile() as capture:
            try:
                sys.stderr.flush()
                os.dup2(capture.fileno(), 2)
                item = profile["text"]
                self.model = Llama(model_path=str(path), n_gpu_layers=-1, logits_all=True,
                                   n_ctx=4096, n_batch=1, n_ubatch=1,
                                   n_threads=item["n_threads"], n_threads_batch=item["n_threads"],
                                   seed=0, verbose=True)
            finally:
                sys.stderr.flush()
                os.dup2(saved_stderr, 2)
                os.close(saved_stderr)
                capture.seek(0)
                log = capture.read().decode("utf-8", errors="replace")
                sys.stderr.write(log)
        self.load_seconds = time.monotonic() - started
        offloads = re.findall(r"offloaded\s+(\d+)/(\d+)\s+layers to GPU", log)
        if not offloads or int(offloads[-1][0]) != int(offloads[-1][1]) or int(offloads[-1][0]) == 0:
            self.model.close()
            raise RuntimeError("full GPU layer offload not established by initialization log")
        self.evidence["offloaded_layers"] = list(map(int, offloads[-1]))
        self.evidence["gpu_allocation"] = allocation_snapshot()
        if not self.evidence["gpu_allocation"]:
            self.model.close()
            raise RuntimeError("model process GPU allocation not observed")
        self.evidence["gpu_buffer_lines"] = [line for line in log.splitlines() if "CUDA" in line and "buffer" in line]
        self.prefix = []
        self.calls = 0
        self.filter_seconds = 0.0
        self.last_diagnostics = {}
        self._special = {}
        self.api = api

    def start(self, context):
        context.decode("utf-8", errors="strict")
        self.prefix = []
        ids = [self.model.token_bos()] + tokenize_bytes(self.model, context)
        if len(ids) + 2048 > 4096:
            raise ValueError("prompt plus carrier exceeds context window")
        evaluate_context(self.model, ids)
        self.calls += len(ids)

    def distribution(self):
        started = time.monotonic()
        scores = np.asarray(self.model.scores[self.model.n_tokens - 1], dtype=np.float64)
        pool = stable_order(scores)[:256]
        raw_q = normalized(scores)
        allowed = []
        for value in pool:
            token = int(value)
            if token not in self._special:
                attributes = self.model._model.token_get_attr(token)
                self._special[token] = bool(attributes & (1 | 2 | 8 | 16))
            if self._special[token] or raw_q[token] == 0:
                continue
            if not detokenize_bytes(self.model, [token]):
                continue
            if consistent_candidate(self.model, self.prefix, token):
                allowed.append(token)
        if not allowed:
            raise ValueError("empty text support after complete-prefix filtering")
        ids = np.sort(np.asarray(allowed, dtype=np.int64))
        q = normalized(scores[ids])
        keep = q > 0
        ids, q = ids[keep], q[keep]
        q /= q.sum(dtype=np.float64)
        order = np.asarray([v for v in allowed if v in ids], dtype=np.int64)
        self.last_diagnostics = {"support": len(ids), "top256_mass": float(raw_q[pool].sum()),
                                 "eligible_mass": float(raw_q[ids].sum())}
        self.filter_seconds += time.monotonic() - started
        return ids, q, order

    def observe(self, token):
        self.model.eval([int(token)])
        self.calls += 1
        self.prefix.append(int(token))

    def serialize(self):
        raw = detokenize_bytes(self.model, self.prefix)
        raw.decode("utf-8", errors="strict")
        if tokenize_bytes(self.model, raw) != self.prefix:
            raise ValueError("final text tokenization changed")
        return raw

    def reconstruct(self, raw):
        if len(raw) > 4 * 1024 * 1024:
            raise ValueError("text artifact exceeds input bound")
        raw.decode("utf-8", errors="strict")
        ids = tokenize_bytes(self.model, raw)
        if not ids or len(ids) > 2048 or detokenize_bytes(self.model, ids) != raw:
            raise ValueError("invalid carrier tokenization or capacity")
        return ids

    def close(self):
        self.model.close()
