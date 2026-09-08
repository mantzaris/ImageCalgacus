# V0 implementation observations

Implementation began 8 September 2026 UTC against ImageCalgacus `9ef074df984bc3974470b05d7224110b8d7f3a7b`. No applicable AGENTS.md was found. Work is V0 only.

## Initial inspection and foundation (chronological observations)

- Seven CPU foundation tests passed: all byte/nibble vectors, packet fields/lengths, parser bounds, AES-256-GCM known vector/authentication failures, UTF-8 limits, nonce collision handling and fresh-run refusal.
- RankCloak source revision: `ce853d42d6ba64065cb63c6bdfc0d825c62734cd`. The local GGUF SHA-256 matches the approved `86c8ea6c8b755687d0b723176fcd0b2411ef80533d23e2a5030f845d13ab2db7`.
- Binary inspection confirms the three GGML CUDA replay controls are present; this is not yet GPU execution evidence. The installed actual KV-clear helper calls `llama_memory_clear(..., True)`.
- The author-linked MEGA folder is accessible with one 214,732,802-byte checkpoint. Download/acquisition is CPU/network work; GPU inference is not yet verified.
- The runtime wrapper conservatively charges complete model-process wall time, including pre-allocation imports/hash checks, and enforces the total 7,200-second limit. No model process is permitted without that wrapper.
- PixelCNN++ adaptation preserves parameter names and architecture; only inference imports, fresh input-device padding and removal of debug/training paths are changed. Exact discrete conditionals replace the upstream approximate likelihood/continuous sampler, as approved.
- Existing RankCloak environments are not modified. A missing text-only Pillow dependency will be isolated inside this project's ignored dependency directory if needed.

## Verified preflight and preliminary results

- Text preflight completed successfully in 19.4269 charged seconds. Initialization reported 33/33 layers offloaded, n_batch=1 and n_ubatch=1; GPU buffer allocation and nonzero per-process SM activity were observed. Two reset/incremental prefix replays had identical top-16 ranks.
- llama.cpp retains a host embedding-lookup buffer while offloading all 33 reported layers. Full offload here means the backend's full-layer profile, not every operation/tensor being on GPU. The compiled USE_GRAPHS capability string is not the effective runtime graph setting; the approved graph-disable environment remains set.
- Image preflight completed in 200.3389 charged seconds. All 567 tensors loaded strictly after bijective removal of the author's DataParallel module. prefix; parameters/input/output were CUDA tensors, evaluation/inference modes were verified, and CUDA convolution/GEMM kernels were recorded. Current/future pixel perturbation at the checked position changed parameters by exactly zero.
- The first ordinary 32×32 PNG took 96.8836 seconds to generate and 97.0272 to replay. Recovered ranks matched throughout; its seed-2001 first row is the fixed shared V0 context. No appearance-based selection occurred.
- Preliminary I1: saved UTF-8 carrier, 616 tokens/2,636 bytes; encode/replay 145.2280/145.9917 seconds; authentication, complete tail, and evaluator equality all passed.
- Preliminary T1: saved PNG, 992 pixels/2,976 channels/2,213 bytes; encode/replay 83.7926/83.5314 seconds; authentication, full canvas and evaluator equality all passed.
- Completed GPU-process charges after preliminary examples: 717.6033 seconds. The pre-ten-case projection is 4,008.4891 seconds including the 25% reserve, below 7,200.
- The runtime status display initially treated a currently active ledger record as an unresolved old record. Status reporting now distinguishes live elapsed time; the serial launch guard remains strict. This was a CPU bookkeeping correction, not a carrier failure or a change to neural replay.
- The receiver rejects undeclared profile fields and extra input-directory files. It imports no sender/demo/evaluator module and does not call the package-wide source hash routine (which would read fixture-bearing source files). A separate evaluator compares literal bytes and checks the frozen source digest.
- Each standalone case encoder is a new encoding run with its own fresh key; the demo groups these runs. No encoding resumes under an old key. No packet bytes, token IDs, rank traces or persistent sender caches are written for receiver use.
- Fifteen focused CPU tests passed before the ten-case run. Application modules are frozen for that run; review/documentation work is separate.

## Final V0 checkpoint

- The ten-case run completed with 10/10 authenticated, complete, exact recoveries, including all five source images and the five UTF-8 lengths. Both preliminary examples also passed; there were 12 stego attempts total, no failed carriers and no rerolls.
- All 26 model processes were charged: 3,163.6531 seconds (52.73 minutes), leaving 67.27 of the approved 120 minutes. GPU work stopped after T5's receiver exited. Every model process has nonzero per-PID GPU activity evidence.
- Application source hash remained `77ef233f9541072dbac0140d11dd84dac1a3494c60fb324b74413a71b25c0400` throughout the ten-case run. Sixteen final CPU tests passed, including an added negative evaluator check; tests/docs/review assembly did not alter the frozen application.
- Routine interface detail: `distribution()` returns observable IDs, normalized probabilities `q`, and stable ordered IDs (not log probabilities). Neural logits/mixture parameters and float64 normalization feed this compact V0 interface. This does not change the packet/rank protocol.
- The first ordinary image's first 96-byte row was independently compared with the retained shared row; equality passed. No new context or fixture selection occurred.
- Local key audit found 12 distinct 32-byte encoding keys; all source and receiver-copy key files have 0600 permissions and the copies match. No key bytes were printed.
- Public review assembly passed its fixed input/profile/context, source-freeze, per-process GPU evidence, budget and key-exclusion checks. Keys, weights, environments and raw logs remain ignored; all generated carriers and recovered viewable outputs are public development artifacts in `artifacts/v0_review/`.
- The vendored PixelCNN++ license notices are explicitly included as package data. No existing RankCloak environment was changed; its only dirty files remain the two pre-existing cover-letter edits observed before work.
- Commands, measurements, limitations and the ten-case table are in [v0_results.md](v0_results.md). V1/V2 were not started; nothing was committed or pushed.
