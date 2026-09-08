# V0 execution results

## Outcome

**V0 acceptance: achieved.** All ten preselected development payloads were attempted once in `runs/ten-001`; 10/10 recovered exactly from the delivered UTF-8/PNG files, with authenticated parsing and complete carriers. The two preliminary I1/T1 examples also passed and are retained separately, not counted as additional independent evaluation cases. 0 stego attempts failed.

Both neural backends executed on the same selected local GPU, sequentially. Sender processes exited before independently launched receiver processes; source equality was checked by a separate CPU evaluator. No V1/V2 work, cloud allocation, model training, commit or push was performed.

The public [review packet](../artifacts/v0_review/README.md) contains every generated stego carrier, original/recovered viewable images or text, compact results, tests, provenance and GPU evidence. Retained decoding keys remain locally in ignored `runs/`, never in the review packet.

## Implemented scope and reuse

The compact `imagecalgacus/` package implements packet handling, fixed radix-16 ranks, GPU text/image adapters, sender, receiver, CPU evaluator, preflight and a serial demonstration runner. A process-wall-time wrapper enforces the 7,200-second V0 allowance. Focused tests, explicit configuration, dependency metadata, acquisition/review scripts and usage documentation accompany it.

The approved packet is unchanged: big-endian `>BBHHH` header (version, kind, byte length, width, height), a zero-padded 256-byte slot, AES-256-GCM with a 12-byte random nonce and 16-byte tag, and AAD `ImageCalgacus/packet/v1`. Thus `12 + 8 + 256 + 16 = 292` transported bytes become exactly 584 high-nibble/low-nibble ranks in 1–16. The receiver knows this fixed size before decoding, authenticates before parsing, and validates dimensions, lengths, UTF-8 and zero padding.

RankCloak was inspected/reused at [`ce853d42d6ba64065cb63c6bdfc0d825c62734cd`](https://github.com/mantzaris/llm-rankcloak/tree/ce853d42d6ba64065cb63c6bdfc0d825c62734cd):

| Earlier component | V0 adaptation |
| --- | --- |
| `model_io.load_llama_cpp_model`, `llama_cpp_gpu_offload_supported`, `preload_pip_cuda_libraries` | Explicit full offload, CUDA capability/library checks and initialization evidence in `text_backend.py`; the original CPU default is not used. |
| `reset_model`, `evaluate_context`, last-logit and exact-byte tokenizer/detokenizer helpers | Actual context/KV clearing between sequences, prompt evaluated once and incremental single-token evaluation within each sequence; exact byte reconstruction. |
| `rank_codec` stable ordering, `encode_bytes_to_bounded_ranks`, `decode_bounded_ranks_to_bytes`, incremental encode/replay pattern | `fixed_rank.py` and independent sender/receiver loops; descending score, ascending observable-ID ties, explicit support failures. |
| Token filtering/replay, NVIDIA README, revision-v3 requirements/reproduction profiles | Matched complete-prefix filtering and pinned numerical/replay controls; no prior research pipeline or source-bearing representation objects. |

No RankCloak application import or implicit sibling source dependency was introduced. Existing interpreter/GGUF paths are explicit configuration; its environments and pre-existing manuscript edits were left unchanged. Attribution and the pixel port's nonstandard non-sale license are preserved in [THIRD_PARTY.md](../THIRD_PARTY.md) and the vendored license files.

## Environment and GPU evidence

Execution used Python 3.10.13 and the physical **NVIDIA RTX 5000 Ada**, UUID `GPU-10d1f16f-9e79-08bb-b2ba-3353c04422cf`, PCI `00000000:09:00.0`, driver 590.48.01, 32,760 MiB total VRAM. It was physical index 1 when inspected and was selected by UUID, mapping to logical CUDA device 0. The separate 4-GB T2000 was not used.

| Backend | Verified identity and observations |
| --- | --- |
| Text | Existing `.venv-generation-v3`: llama-cpp-python 0.3.23, CUDA runtime 12.4.127, cuBLAS 12.4.5.8. Llama 3 8B Instruct Q4_K_M GGUF SHA-256 `86c8ea6c8b755687d0b723176fcd0b2411ef80533d23e2a5030f845d13ab2db7`. |
| Image | Existing `.venv`: PyTorch 2.5.1+cu124. CIFAR-10 PixelCNN++: 5 residual blocks, 160 filters, 10 mixtures; checkpoint SHA-256 `a5ed558f6d4098ce3cbfd47658b7e3be37fae77b71a90c8a56f46a6266ff833f`, 214,732,802 bytes. |
| CPU support | NumPy 2.2.6, cryptography 46.0.7, Pillow 12.3.0. Missing text-environment Pillow was installed into this project's ignored `.deps-text/` only. |

The [preflight records](../artifacts/v0_review/preflight/) and [per-process GPU summary](../artifacts/v0_review/gpu_evidence.json) establish more than device visibility/configuration flags:

- Text initialization reported **33/33 layers offloaded**, CUDA model/KV buffers and PID-specific GPU allocation. Nonzero per-process SM activity was recorded during inference. Two reset/incremental prefix replays had identical top-16 ranks.
- The full-offload profile explicitly sets `n_gpu_layers=-1`, `logits_all=True`, `n_batch=n_ubatch=1`, `n_ctx=4096`. CUDA graphs/fusion are disabled; FP32 cuBLAS, deterministic workspace and launch-blocking controls are retained. The binary exposes the required control names. Full reset clears actual KV state; the neural prefix is not recomputed from scratch at each token.
- llama.cpp still uses a host embedding-lookup buffer: “full offload” describes all 33 reported layers, not every operation or tensor. CPU tokenization/probability bookkeeping is intentional and charged while the model process exists.
- Image loading strictly matched all **567 tensors** after bijectively stripping the author's uniform `module.` namespace. Parameters/buffers and model inputs/outputs were CUDA-placed; evaluation and inference modes were active, TF32/autocast were not used, and CUDA convolution/GEMM kernel events were observed.
- Current/future-pixel perturbation at the tested location produced exactly zero change in current parameters; repeated GPU forward outputs matched. The first ordinary 32×32 canvas generated in 96.884 seconds and replayed in 97.027 seconds with identical ranks. This is a focused causal check, not an exhaustive proof over all inputs.

GPU capability, memory, profile, model hash, placement or inference failures are explicit failures. There is no CPU retry, partial-offload retry or concurrent backend service.

The pixel model is adapted from [`pclucas14/pixel-cnn-pp@7cb4436f062fda9b63ecc9e3b75d2c2dcb379931`](https://github.com/pclucas14/pixel-cnn-pp/tree/7cb4436f062fda9b63ecc9e3b75d2c2dcb379931). The checkpoint came from its author-linked public MEGA folder, without TensorFlow repair, weight conversion or training. The local hash is recorded; no author-published checksum or separate checkpoint license notice was observed. Weights are retained locally, not redistributed.

## Artifact and receiver contract

Text uses the one fixed forest-journal prompt, separately tokenized with one BOS. Carrier tokenization uses no BOS/special-token parsing. All packet and completion candidates pass strict UTF-8 and complete-prefix `T(D(prefix + candidate)) == prefix + candidate`; stable ranks come from the approved top-256-before-filtering pool. Successful carriers contain **584 packet tokens + 32 ordinary completion tokens = 616**.

Images use the first row of the first ordinary seed-2001 canvas as the shared 96-byte prefix. That row is supplied separately, not delivered in the carrier. Delivered PNGs are **32 pixels wide × 31 high, RGB8**, containing 992 pixels/2,976 channel values in raster R/G/B order. There are 584 packet channels and **2,392 ordinary completion channels**, including the unfinished packet-ending pixel. Exact discretized logistic-bin probabilities and R→G→B mixture posterior updates are used; neither a density approximation nor inaccessible latent codes are decoded. Lossless PNG save/load checks compare pixel bytes.

The receiver reconstructs tokens from saved UTF-8 bytes and channels from saved PNG pixels. Its input directory contains only carrier, profile, fixed context and retained key; outputs/reports are elsewhere. The [input audit](../artifacts/v0_review/receiver_input_checks.json) and focused import/data-flow tests confirm the declared boundary. No source bytes/digests, original packet bytes, saved token IDs, latents, rank traces, evaluator manifests or sender caches are receiver inputs. This is fresh-process data separation, not an OS sandbox.

Each standalone case encoding is a new private run, with an OS-random key and random nonce checked for duplicates. The outer demo groups those case runs. Encoding never resumes under an old key; sampling seeds do not generate keys/nonces. A final local check found 12 distinct 32-byte encoding keys, private 0600 key permissions and matching receiver copies, without printing any key material. The evaluator independently compares literal source/recovered bytes, the frozen fixture digest and parsed dimensions; authentication alone cannot satisfy equality.

## Ten-case evaluation

Fixtures were frozen before carrier inspection. Every image has 256 canonical grayscale bytes; texts are 32/48/64/96/128 bytes, including T3's accented UTF-8. No case was replaced or rerolled.

| Case | Direction | Source bytes | Carrier bytes | Encode s | Decode s | Auth / complete / exact |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| I1 | image → text | 256 | 2840 | 148.102 | 148.350 | pass / pass / pass |
| I2 | image → text | 256 | 2603 | 136.755 | 137.459 | pass / pass / pass |
| I3 | image → text | 256 | 2937 | 136.717 | 137.743 | pass / pass / pass |
| I4 | image → text | 256 | 2531 | 140.189 | 138.772 | pass / pass / pass |
| I5 | image → text | 256 | 2573 | 141.693 | 142.083 | pass / pass / pass |
| T1 | text → PNG | 32 | 2232 | 84.456 | 84.154 | pass / pass / pass |
| T2 | text → PNG | 48 | 2362 | 84.181 | 84.731 | pass / pass / pass |
| T3 | text → PNG | 64 | 2282 | 85.086 | 83.826 | pass / pass / pass |
| T4 | text → PNG | 96 | 2347 | 83.997 | 83.843 | pass / pass / pass |
| T5 | text → PNG | 128 | 2533 | 84.336 | 84.112 | pass / pass / pass |

Image-to-text counts are 616 tokens per carrier. Text-to-image counts are 992 pixels and 2,976 channels per carrier; these units must not be interchanged. Encode/decode columns measure the generation/replay region, including CPU filtering/bookkeeping and completion but excluding cold model loading. Per-case JSON separately records load/total times, model calls, hashes and GPU evidence. The budget below uses the larger complete subprocess wall times.

The preliminary I1 example took 145.228/145.992 seconds to encode/replay; preliminary T1 took 83.793/83.531 seconds. Their independent equality/authentication/completion checks passed before the ten-case run.

## Verification and measured budget

**16 focused CPU tests passed** in the final captured run, with no neural CPU inference. They cover all 256 high/low-nibble vectors, strict packet sizes/header order/parser bounds, an independent AES-GCM known vector, authentication/wrong key/AAD failures, UTF-8 limits, fresh keys/duplicate-nonce handling, rank/support bounds, complete-prefix versus singleton counterexamples, actual KV-clear invocation, PNG pixel preservation/mode/truncation rejection, CPU/partial profiles and extra receiver inputs. Pixel PMFs are checked against high-precision Decimal CDF values and an independently factored RGB joint distribution. A negative evaluator test proves authenticated-but-different bytes, or substituted frozen sources, cannot pass.

Actual model-backed evidence consists of both GPU preflights, two preliminary artifact recoveries and the ten final fresh-process recoveries. Application source was frozen across the final run: `77ef233f9541072dbac0140d11dd84dac1a3494c60fb324b74413a71b25c0400`. Tests/review documentation added no neural-model changes.

| Charged work | Complete process seconds |
| --- | ---: |
| Text preflight | 19.427 |
| Image preflight, ordinary canvas and replay | 200.339 |
| Preliminary encoding, both directions | 248.892 |
| Preliminary independent replay, both directions | 248.946 |
| Ten-case text generation (five) | 782.957 |
| Ten-case text replay (five) | 783.262 |
| Ten-case PNG generation (five) | 440.758 |
| Ten-case PNG replay (five) | 439.073 |
| **Total** | **3163.653** |

Total charged GPU allowance: **52.73 minutes (0.8788 GPU-hours)** of the approved 120 minutes; **67.27 minutes remained**. All 26 model processes are accounted for, including loading, imports/hash checks, CPU-side filtering while models were resident, inference, replay and teardown. This is conservative occupied-process accounting, not a claim of continuous GPU-kernel utilization. CPU tests, downloads and documentation do not consume GPU inference time.

Before the ten cases, the measured preliminary pair costs were 323.129 seconds for text and 174.708 for image; preflight/preliminary spend was 717.603 seconds. The recorded projection was `1.25 × [717.603 + 5 × (323.129 + 174.708)] = 4,008.489 seconds`, including a 25% reserve, below the cap. No allowance extension or additional hardware was needed.

## Commands that ran successfully

Run from the repository root; these are historical commands, not instructions to overwrite or resume their existing output directories. The full sender/receiver subprocess commands and PIDs are in [gpu_evidence.json](../artifacts/v0_review/gpu_evidence.json); each receiver was launched only after its sender exited.

```bash
# CPU tests
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m unittest discover -s tests -v

# Fixture freezing and sequential examples/evaluation
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.demo --prepare
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.demo --mode preliminary --cases configs/v0_cases.json --profile configs/v0.json --new-run runs/preliminary-001
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.demo --mode ten --pilot runs/preliminary-001 --cases configs/v0_cases.json --profile configs/v0.json --new-run runs/ten-001
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.evaluate --run runs/ten-001 --references runs/ten-001/references.json

# CPU-only public review assembly
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/collect_v0_review.py --run runs/ten-001 --preliminary runs/preliminary-001
```

[README.md](../README.md) records the successful preflight, checkpoint acquisition, isolated dependency installation, shared-row copy, and standalone encode/decode interfaces. A new encoding attempt requires a new directory/key and available allowance; retained artifacts may be decoded using their private retained keys.

## Failures, corrections and limitations

- No GPU preflight, preliminary artifact or final stego attempt failed; no fixture substitutions, outcome-based rerolls or hidden retries occurred. All artifacts, including the first ordinary image, are retained.
- CPU-side integration corrections were made before the final application freeze: handle the author's DataParallel namespace with strict loading; install only the missing local Pillow dependency; distinguish an actively running budget record from an abandoned one in the status display; reject undeclared receiver profile fields. These are not successful/failed additional stego observations.
- The ordinary sandbox command launcher failed before running commands (`bwrap` loopback setup). Authorized tool escalation was used; no environment access controls were disabled and no OS isolation claim is made.
- Routine implementation choices are documented in [v0_implementation.md](v0_implementation.md). Backend distributions return normalized probability vectors `q` plus stable ordered IDs; the V0 coder consumes ranks. Per-case fresh encoding keys are stricter than sharing one key across a demo batch. Neither changes the scientific protocol.
- Compatibility and repeatable recovery are established only for this pinned host/profile and these ten fixtures. Cross-device/runtime behavior, text naturalness, image imperceptibility, robustness and statistical reliability remain unverified. AEAD provides authentication, not steganographic undetectability.
- The required V1 entropy/arithmetic methods, their finite-stream verification, full development data/calibration and V2 controls/statistics/detection/paper evidence remain **unimplemented and unexecuted**. Work stops at the V0 checkpoint.
