# Implementation plan: GPU-first text/image transport

Revised for independent review, 7 September 2026. Planning only: no application changes, installations, weight downloads, inference runs or resource allocations were performed.

**V1.1 amendment, 8 September 2026:** V0 and the V1 implementation/pilot are accepted checkpoints; V1 remains unqualified. The historical inspection below is not a description of today's implemented repository. The authorized prospective main-study reduction is **20 held-out images + 20 held-out texts, one existing context/direction, all three methods = 120 stego units**, with up to **40 independent shared ordinary traces**. Measured runtime motivates the reduction; protocol, profiles, payloads, recovery and V1 qualification are unchanged. This is a focused feasibility study, not a statistical-power claim. [Results/remaining conditions](../notes/v1_1_results.md) and [new forecast](../artifacts/v1_1_review/compute_projection.json) supplement, and do not overwrite, accepted V0/V1 evidence.

**V1.2 implementation clarification, 8 September 2026:** source/context preparation and the development-only singleton arm are implemented without changing the main protocol. Frozen source bytes/offsets are in `data/qualification_v1/manifest.json`; `configs/v1_qualification.json` resolves all 152 development units, 16 ordinary traces and up to 48 shared controls. The 12 accepted pilot work IDs, four calibration traces and two controls are credited once (140/12/46 initially pending); diagnostic replays are not credits. The default remains complete-prefix eligibility; `configs/v1_fixed_static.json` opts into singleton consistency and retains delivered UTF-8 even with tokenization drift. Prompt2 is the exact soup prompt in the source manifest; row2 is payload-independent PCG64(2002) RGB8 bytes. No threshold, model, packet, carrier cap, completion, A1 rule or held-out allocation changes. New observed outcomes and pending counts are in [V1.2 results](../notes/v1_2_results.md). This checkpoint authorizes only the six frozen units in `configs/v1_2_batch.json`, within the existing V1 balance, not full qualification or V2.

## 1. Releases and scientific authority

| Component | Required for V0 | Later release | Reason |
| --- | --- | --- | --- |
| Verified GPU text and pixel inference; one model each | Yes | Same pinned backends | Both directions must actually work |
| 292-byte authenticated packet, fixed radix-16 coder | Yes | Unchanged protocol | Small common foundation |
| Saved UTF-8/PNG, fresh receiver, separate byte evaluator | Yes | Expanded evaluation | Artifact recovery is the endpoint |
| One prompt, one shared row, five development payloads/direction | Yes | V1 expands development | Ten-case functionality demonstration |
| Entropy gating and arithmetic comparator | No | V1, mandatory before V2 | Not prerequisites for first recoveries |
| Static-mask comparison, datasets, calibration, compute projection | No | V1 | Establish complete-study readiness |
| Resumption and persistent experiment bookkeeping | No | V1 as needed | V0 starts fresh encoding runs |
| Matched controls, intervals, detection, figures, paper evidence | No | V2 | Ten cases cannot establish research claims |

The scientific specification is [crossmodal_steganography_focused_research_plan.md](crossmodal_steganography_focused_research_plan.md). Baseline inspection is repository commit `16ce203e11a1206081801cd36f501d92a04ff753`. The original implementation plan added a labeled prototype-sequencing clarification; V1.1 additionally makes the narrow prospective allocation amendment above. Both directions, three final methods, payload conventions, recovery contract, approximately six researcher-weeks and **40 GPU-hours overall** remain unchanged. The main allocation alone is superseded by the labeled V1.1 amendment above.

V0 establishes functionality on the tested GPU/runtime configuration, not imperceptibility, broad robustness, statistical reliability or a completed journal study. Gates are technical acceptance checks, not repeated approval requests after implementation is authorized. A material scope change still requires review.

## 2. Inspected starting point and reuse

The repository contains two plans, MIT license (2026, a.v.mantzaris), effectively empty `.gitignore` and its backup; `notes/` is empty. There is no application, dependency declaration, tests, runtime configuration or local model here. No applicable `AGENTS.md` was found in the repository or checked ancestors. Proposed components are new here, with identified external adaptations. Reserve `notes/` for subsequent implementation observations.

The primary reference is the local sibling `../llm-rankcloak`, inspected at [`ce853d42d6ba64065cb63c6bdfc0d825c62734cd`](https://github.com/mantzaris/llm-rankcloak/tree/ce853d42d6ba64065cb63c6bdfc0d825c62734cd). Relevant files were unmodified; unrelated edits were untouched.

| Existing file/function at that revision | Adaptation → project component |
| --- | --- |
| `rankcloak/model_io.py::load_llama_cpp_model`, `llama_cpp_gpu_offload_supported` | Change CPU default `n_gpu_layers=0` to required `-1`; preserve capability failure and add observed offload checks → `text_backend.py`, `preflight.py` |
| `preload_pip_cuda_libraries` | Load pip CUDA runtime/cuBLAS libraries globally before importing llama.cpp; report loaded paths and unresolved dependencies → text preflight |
| `reset_model`, `evaluate_context`, `get_last_logits` | Clear Python/context and actual KV state between sequences; evaluate context once, then one token incrementally → text sender/replay |
| `detokenize_bytes`, `tokenize_payload_text` | Preserve exact bytes and explicit no-BOS/no-special carrier tokenization; replace implicit prompt conventions. Never serialize `safe_detokenize` replacement text → text artifact I/O |
| `rankcloak/rank_codec.py::sorted_token_ids_from_logits`, `rank_of_token`, `token_id_at_rank` | Descending logits, ascending ID for exact ties, one-based ranks → `fixed_rank.py` |
| `encode_bytes_to_bounded_ranks`, `decode_bounded_ranks_to_bytes` | Adapt radix-16 high/low nibble bridge; replace source-metadata-dependent permissive truncation with exactly 584 ranks → fixed coder |
| `generate_token_ids_from_ranks`, `rank_trace_from_token_ids`, `recover_ranks_from_generated_ids` | Reuse context-once/`model.eval([id])` schedule; receiver IDs must come from delivered bytes → text backend |
| `token_filters.py::choose_token_at_rank_with_optional_filter`, `rank_token_with_optional_filter` | Reuse matched filtered ordering/inversion, not the prose blacklist; eligibility becomes complete-prefix consistency → text backend |
| `revision_protocol.py::generate_rank_span`, `recover_rank_span`, `retokenize_message`, `build_round_trip_stable_mask` | Reuse serial replay pattern; replace saved span offsets with packet-count framing. Singleton mask is V1 baseline only; exclude source-bearing `Representation`/`decode_representation` |
| README “NVIDIA GPU Setup”; `configs/revision_v3/generation_requirements.json`; `configs/revision_v1/models.json`; `environment/revision_v1/{README.md,REPRODUCE.md,determinism.json,requirements-lock.txt}` | Adapt CUDA installation evidence, serial loading, batch and numerical controls below; do not copy the earlier model matrix, GPU identifiers, cloud instructions, budgets or authorizations |

Local read-only checks found Python 3.10.13 and driver 590.48.01; RTX 5000 Ada, 32,760 MiB total/32,220 MiB free, and T2000, 4,096/3,638 MiB. Free memory is a transient observation, not a reservation or proof of offload. RankCloak's `.venv-generation-v3` has `llama-cpp-python 0.3.23`, CUDA shared libraries, `nvidia-cuda-runtime-cu12 12.4.127` and `nvidia-cublas-cu12 12.4.5.8`, but no PyTorch/Pillow. Its `.venv` has PyTorch `2.5.1+cu124` and Pillow `12.3.0`, but no llama-cpp package. Both have NumPy `2.2.6` and cryptography `46.0.7`. Neither inspected environment has TensorFlow; `nvcc`/`cmake` were not on the inspected PATH.

Prefer these interpreters if verified compatible; separate text/image environments are acceptable. Declare dependencies here, configure interpreter paths explicitly, and avoid unreviewed shared-environment changes or sibling imports.

The sibling Llama 3 8B Q4_K_M GGUF exists (4,920,734,272 bytes). RankCloak records QuantFactory revision `a06c33ec89c1e3402009fb47f466a89127c6d223` and expected SHA-256 `86c8ea6c8b755687d0b723176fcd0b2411ef80533d23e2a5030f845d13ab2db7`; this turn checked size, not content hash or loading. Verify model terms and hash before adoption. No image checkpoint was identified in the inspected project/sibling model directories.

Record adapted files, revisions, citations and complete notices in future `THIRD_PARTY.md`; RankCloak's MIT notice must accompany reused code. Do not import the research pipeline. [Calgacus](https://arxiv.org/html/2510.20075v1), the bounded-byte bridge, entropy gating, arithmetic steganography and [tokenization-consistency verification](https://aclanthology.org/2025.emnlp-main.361/) are prior work. RankCloak's reported saved-ID recovery does not verify this endpoint. Explore (`b9f1650b4eb0b2261b0080f86d9b1d8fadedbc0b`) remains background, not a payload-conversion dependency.

## 3. V0 GPU and image feasibility first

### Required text profile and replay

Explicitly require `n_gpu_layers=-1`, `logits_all=True`, `n_batch=1`, `n_ubatch=1`, `n_ctx=4096`, and a pinned thread count. Ordinary commands reject CPU inference; missing capability, partial offload, OOM or CUDA execution errors terminate clearly. No CPU retry. Partial offload requires a recorded, reviewed departure and renewed replay checks.

Small numerical or context-state changes can reorder near-tied logits and break decoding. Before backend imports, validate RankCloak's GPU replay settings:

| Setting | Value and purpose |
| --- | --- |
| `CUDA_LAUNCH_BLOCKING` | `1`: synchronous launch behavior |
| `GGML_CUDA_DISABLE_GRAPHS` | `1`: avoid graph-dependent execution differences |
| `GGML_CUDA_DISABLE_FUSION` | `1`: fixed unfused replay path |
| `GGML_CUDA_FORCE_CUBLAS_COMPUTE_32F` | `1`: recorded compute-precision control |
| `CUBLAS_WORKSPACE_CONFIG` | `:4096:8`: reproducible workspace configuration |
| `CUDA_DEVICE_ORDER` / `CUDA_VISIBLE_DEVICES` | `PCI_BUS_ID` / selected physical UUID; only that GPU is exposed, mapped to logical 0 |

Unlike upstream `setdefault`, profile validation must reject conflicting effective values. Check whether the selected backend build actually supports these controls; recording ignored variables is insufficient. Retain them until independent GPU replay passes; throughput alone does not justify removing them.

The inspected installation recipe uses the CUDA 12.4 wheel for llama-cpp-python 0.3.23 and the two pinned NVIDIA packages above. `preload_pip_cuda_libraries` loads `libcudart.so.12`, `libcublasLt.so.12`, `libcublas.so.12` with `RTLD_GLOBAL`. Confirm actual loaded library paths, build identity and architecture support. If installation later proves necessary, verify a compatible CUDA wheel or a source build with `CMAKE_ARGS="-DGGML_CUDA=on"`; historical pins are evidence, not universal compatibility guarantees. [Official installation documentation](https://llama-cpp-python.readthedocs.io/en/latest/#installation-configuration) distinguishes CUDA builds from CPU builds.

At sequence start adapt `reset_model`: both `model.reset()` and the supported actual KV-clear operation must succeed; do not silently skip a missing private API. Then `evaluate_context` once and incremental `model.eval([id])` thereafter, identically at sender/receiver. CPU full-prefix **tokenizer** checks do not imply full-prefix neural reevaluation.

### Fail-fast preflight evidence

Record the selected physical UUID/PCI bus/name, current free memory, driver, logical mapping, interpreter, dependency/build/library hashes, model/tokenizer hashes and effective profile. Never copy old visibility values or assume physical device 0.

Text preflight must show CUDA backend linkage/system information, `llama_cpp_gpu_offload_supported()`, backend initialization reporting all eligible model layers offloaded, model GPU buffers, and a successful short evaluation. Correlate its PID/device allocation with execution evidence (CUDA kernel trace or backend timings plus process-specific GPU activity). Flags, GPU visibility and PyTorch CUDA availability alone cannot pass.

For PyTorch, require `load_state_dict(..., strict=True)` with no missing/unexpected tensors; use `model.to(selected_cuda_device)`, matching inputs/buffers, `model.eval()` and `torch.inference_mode()`. Inspect actual tensor devices, GPU allocation, synchronized inference and CUDA operator execution; record outputs and peak memory. Pin float32 inference, disable autocast/TF32 and cuDNN benchmarking, request deterministic algorithms, and fail on unsupported execution. CPU float64 probability bookkeeping is allowed. Legacy padding allocations must follow the input device, not unqualified default-device calls.

Run text and image jobs sequentially; terminate/release one backend before loading another, including sender versus receiver where necessary. No multi-GPU scheduling or model services. Cross-process equality of selected ranks on small replay fixtures is required in addition to allocation evidence.

### Image candidate decision

Prefer the shortest credible path to correct GPU execution, first investigating the [PyTorch PixelCNN++ port](https://github.com/pclucas14/pixel-cnn-pp/tree/7cb4436f062fda9b63ecc9e3b75d2c2dcb379931), revision `7cb4436f062fda9b63ecc9e3b75d2c2dcb379931`, because a CUDA PyTorch environment exists. Inspect/adapt `model.py::PixelCNN.forward` and `utils.py::discretized_mix_logistic_loss`; do not use `load_part_of_model` or its continuous RGB sampler. Match checkpoint architecture: constructor default 80 filters differs from training's 160; strict loading must reject mismatches. Its README advertises weights and reports results, but those are not verified availability/suitability. Its [license](https://github.com/pclucas14/pixel-cnn-pp/blob/7cb4436f062fda9b63ecc9e3b75d2c2dcb379931/license.md) restricts selling despite an MIT heading; preserve its separate license, do not relicense it under this project's MIT notice, and resolve checkpoint terms.

The bounded alternative is [official PixelCNN++](https://github.com/openai/pixel-cnn/tree/bbc15688dd37934a12c2759cf2b34975e15901d9), revision `bbc15688dd37934a12c2759cf2b34975e15901d9`, with advertised CIFAR-10 checkpoint and legacy `tensorflow.contrib`. Choose it only if a compatible GPU runtime/checkpoint is readily usable. Preserve its notices and required inference/EMA tensors. Keep only the selected implementation; a legacy backend needs equivalent GPU-operation evidence.

Track separately: published checkpoint availability, actual accessible/local bytes and hash, usage terms, strict runtime compatibility, and experimentally verified conditional/replay suitability. Allow about one day initially, at most **three working days total** for unresolved problems across these candidates. Require normalization/causality checks, one ordinary full 32×32 generation and measured generation/replay costs. No extensive TensorFlow repair, conversion infrastructure, replacement training, latent recovery substitute or one-direction completion claim. If blocked, preserve completed work and report the exact obstacle.

## 4. Compact V0 architecture and commands

Use `imagecalgacus/` with the following modules; no plugin registry or unused framework.

| Proposed module | Contract/dependencies |
| --- | --- |
| `packet.py` | Canonical source validation, `seal(payload, key, nonce)->bytes[292]`, authenticated `open_packet`; cryptography |
| `fixed_rank.py` | Pure nibble conversion and deterministic ordering; NumPy |
| `text_backend.py`, `image_backend.py` | GPU inference, observable distributions and strict artifact I/O; llama-cpp or selected image runtime, Pillow |
| `sender.py`, `receiver.py` | Explicit encode/decode entry points; packet/coder/backend only |
| `preflight.py` | Device/backend evidence and compatibility checks |
| `demo.py`, `evaluate.py` | Preselected cases, serial subprocesses/results; source comparison only in evaluator |

Backend contract: `start(context)`, `distribution()->(observable_ids, log_probs, ordered_ids)`, `observe(symbol)`, `close()`. It accepts no payload. V0 calls the fixed coder; V1 adds gated/arithmetic state machines without changing artifact boundaries. Add focused `tests/`, configurations, dependency/usage/attribution files, and `.gitignore` exclusions for private runs, keys and models.

Planned command interfaces (placeholders resolved during implementation; interpreters/profile paths explicit):

```text
<python> -m imagecalgacus.preflight --profile configs/v0.json --gpu <physical-uuid>
<text-python> -m imagecalgacus.sender image-to-text --source image.png --profile configs/v0.json --context prompt.txt --new-run <new-directory>
<text-python> -m imagecalgacus.receiver image-to-text --carrier inbox/carrier.txt --profile inbox/profile.json --context inbox/prompt.txt --key inbox/run.key --output recovered.gray
<image-python> -m imagecalgacus.sender text-to-image --source message.txt --profile configs/v0.json --context row.rgb --new-run <different-new-directory>
<image-python> -m imagecalgacus.receiver text-to-image --carrier inbox/carrier.png --profile inbox/profile.json --context inbox/row.rgb --key inbox/run.key --output recovered.txt
<python> -m imagecalgacus.demo --cases configs/v0_cases.json --profile configs/v0.json --new-run <demo-directory>
<python> -m imagecalgacus.evaluate --run <demo-directory> --references <private-manifest>
```

All model commands enforce the resolved profile's selected GPU UUID and revalidate it before loading. Preflight dispatches each configured interpreter sequentially. Model paths are explicit configuration, not implicit sibling lookup/download. Sender commands create a new run and key; decoding never creates an encoding run.

Public profiles contain format/AAD, coder, model/runtime identities, dimensions, ordering and budgets. Shared conditioning is exact prompt bytes or the 96-byte row, distinct from the cryptographic key. Per-message transport contains nonce/ciphertext/tag only. Sender diagnostics may contain packet bytes, IDs and ranks; evaluator references contain source bytes/digests, case provenance and expected dimensions.

Stage only carrier, profile, context and retained key in a receiver input directory; declared model/runtime assets are separately readable. Launch a fresh receiver process with explicit paths, not the demo/reference manifest. Inspect imports/data flow to exclude evaluator dependencies. Demonstrate decoding after the sender exits and with diagnostic files/caches absent. Original payloads/digests/packet bytes, saved token IDs, original latents, rank traces and payload-specific sidecars never enter receiver inputs. Runtime/KV caching within its own process is allowed. No new OS sandbox, isolation launcher, sentinel suite or container framework blocks V0. Existing access controls remain intact; this is data separation, not adversarial isolation.

Each new demonstration encoding run creates a fresh OS-random 32-byte key and new directory. Generate random 12-byte nonces, checking an in-memory per-run set and redrawing duplicates before encryption. Retain the key locally with restrictive permissions outside version control; never log key bytes. One live demo batch may share its run key; refuse later encoding resumption/appending. Existing artifacts may be decoded with their retained key. Sampling seeds never generate keys/nonces. Durable cross-run nonce services and transactional scheduling are deferred.

## 5. Packet, rank and artifact correctness

### Fixed packet and probability rules

Unsigned big-endian fields, no alignment:

| Plaintext offset | Bytes | Permitted value |
| --- | ---: | --- |
| 0 | 1 | Version 1 |
| 1 | 1 | Kind 1: UTF-8; kind 2: grayscale |
| 2 | 2 | Actual length: text 32–128; image 256 |
| 4 | 2 | Width: text 0; image 16 |
| 6 | 2 | Height: text 0; image 16 |
| 8 | 256 | Payload, then zero slot padding |

Image reference is canonical 16×16 uint8 grayscale, row-major, not its original container bytes. Text is literal strict UTF-8 without normalization, added spaces, newline conversion or replacement. Authenticate before exposing/parsing plaintext; validate direction/kind, dimensions, bounds, UTF-8 and every padding byte.

Use standard AES-256-GCM, 16-byte tag, AAD exactly `ImageCalgacus/packet/v1` without newline. Transport `nonce || ciphertext || tag`: `12+(8+256)+16=292` bytes = 2,336 bits. Reject 291/293-byte inputs, unknown fields and surplus data. The receiver knows 292 before decoding, so encrypted length causes no framing cycle. Authentication failure returns no partial plaintext. Framing costs 36 bytes; slot padding costs `256-L` bytes (128–224 for text). Remove only authenticated, verified padding using the declared length.

Each byte maps high nibble then low nibble `d` to rank `d+1`: 584 packet symbols, ranks 1–16, no alignment padding. Reject missing/excess ranks and out-of-alphabet values. Stop packet collection by this count, not a sender offset.

Compute eligible probabilities in float64 with stable log-sum-exp and ascending-ID summation. Text ordering uses descending logits as in RankCloak; pixel ordering uses descending log probability; exact ties use ascending observable ID. Freeze that ordering independently of rounded probability displays. Reject NaN/+infinity, empty support or invalid normalization; exclude numerical zero mass and renormalize, recording loss. No arbitrary probability floors. Ordinary sampling uses temperature 1, PCG64 inverse CDF in ID order, no nucleus sampling. Receiver seeds are unnecessary because observations drive replay. Pending fixed packets require at least 16 eligible symbols; completion requires nonempty support. Insufficient support, malformed inputs, numerical errors, deadlines or capacity exhaustion are explicit failures, not retries with wider support.

### Text

Use the pinned embedded GGUF tokenizer. `T(bytes)` explicitly disables BOS insertion/special interpretation; `D(ids)` returns exact bytes without cleanup or replacement. Require support for these flags. Model context is one BOS followed by `T(prompt)`, without chat template/EOS. Tokenize the carrier separately; never retokenize prompt-plus-carrier strings. Verify prompt IDs plus the 2,048 output cap fit `n_ctx=4096`.

At every step, rank the top 256 model IDs **before** filtering. Reject special/control/BOS/EOS IDs and empty renderings. For every candidate require strict UTF-8 and `T(D(s+[v])) == s+[v]` for the complete carrier prefix. Do not add RankCloak's prose blacklist. Apply the same rule to payload, V1 skips/arithmetic steps, and completion. Write exact final bytes, with no inserted BOM/newline. Receiver reads strict UTF-8, checks `D(T(file))==file`, reconstructs each prefix and repeats eligibility from delivered bytes.

Complete the packet, then generate exactly 32 ordinary tokens; total cap 2,048. A packet finishing after 2,016 is packet-complete but carrier-incomplete; do not truncate an unfinished packet to reserve a tail or extend the cap. Recovery/equality can still be reported separately for an incomplete carrier. V0 successful text is exactly `584+32=616` tokens; useful image rate is `2048/616≈3.325` bits/token. Receiver checks the whole carrier including the tail.

### Pixels

Use native 32×32 RGB uint8. Prepend one shared 1×32 row internally, generate rows 1–31 in raster order, R/G/B. Deliver **width 32, height 31** RGB PNG: 992 pixels/2,976 channel values. Receiver reconstructs all symbols from delivered pixels and the shared row, never latents.

A 10-mixture RGB PixelCNN++ emits 100 parameters/pixel: 10 mixture logits and 30 each means, log-scales and coefficients, not 256 categorical logits. Following its likelihood parameterization, clamp log scales at −7, tanh RGB coefficients, and set `x(v)=2v/255−1`. Component mass is the logistic CDF difference over half-bin width `1/255`; 0/255 include infinite tails. Use stable log-CDF calculations, not density approximations or continuous sampling.

For component masses `f` and weights `w=softmax(mixture_logits)`:

`q_R(r)=Σw_k f_Rk(r)`; update `w_k^R ∝ w_k f_Rk(r)`.

`μ_G'=μ_G+c_RG x(r)`; `q_G(g|r)=Σw_k^R f_Gk(g;μ_G')`; update `w_k^RG ∝ w_k^R f_Gk(g;μ_G')`.

`μ_B'=μ_B+c_RB x(r)+c_GB x(g)`; `q_B(b|r,g)=Σw_k^RG f_Bk(b;μ_B')`.

Normalize posterior weights after each observation. Independently compare the conditional product with the joint mixture. Record differences from the upstream loss's small-mass approximation; this discrete adapter is not bit-identical reproduction of that approximation.

Use one GPU network evaluation per visible pixel, caching parameters only within RGB after causal tests establish independence from current/future pixels. Initialize unknown byte values to zero before scaling; reset canvas/padding state per sequence. Same serial schedule at receiver, including full-canvas conformance replay. Finish every channel after packet stop, including a partial pixel: `2976−584=2392` completion channels. Cap exhaustion before packet stop fails.

Pillow must preserve every sample through lossless 8-bit truecolor PNG; reject palette/alpha/wrong dimensions rather than silently converting. No packet metadata, gamma/ICC transformations or trailing payload channel. Check file and pixel-array hashes separately. For 128 source bytes, useful rate is `1024/992≈1.032` bits/pixel, or `1024/2976≈0.344` bits/channel. The pre-shared row costs 96 bytes/context separately.

## 6. V0 cases, milestones and verification

Freeze five grayscale cases with zero-based row r/column c: I1, 17c; I2, 255((r+c) mod 2); I3, floor(255(r+c)/30); I4, 255 inside rows/columns 4–11 and zero elsewhere; I5, PCG64(seed=20260907) uniform uint8 bytes in raster order. Freeze generator/version and canonical bytes before output inspection.

The five text cases are exact UTF-8 below, without surrounding quotes or added newline; validate byte counts/digests before generation. All ten cases are development-only.

| Case / bytes | Source text |
| --- | --- |
| T1 / 32 | Meet me beside the old oak tree. |
| T2 / 48 | Bring the blue notebook to our meeting tomorrow. |
| T3 / 64 | Le café est ouvert; retrouvons-nous près du vieux pont à midi |
| T4 / 96 | The river is quiet tonight. Please leave the blue notebook beside the window before you go home. |
| T5 / 128 | We will meet after the rain has stopped. Bring a notebook, two pencils, and the small map showing the paths through the forests. |

One fixed prompt is “Write a calm field-journal entry about a walk through a temperate forest. Use continuous prose.” Store those exact bytes without quote marks. Take the first row of the first ordinary feasibility image using context seed 2001; freeze it without appearance-based rerolls. Conditioning is payload-independent.

First obtain one saved-file recovery per direction, then a new ten-case demonstration run with five/direction. Preliminary examples may use the first selected cases but are not extra independent observations; budget their two artifacts separately. Do not replace failures with easier inputs. Retain carriers, failed prefixes, errors and lineage. Never reroll keys/nonces for success; repeat only after a documented correction, with a new run/key. Incomplete pixel prefixes are diagnostics, not zero-filled carriers.

| Milestone | Components, tasks and observable outputs | Effort; risk; stopping rule; deferred work |
| --- | --- | --- |
| **V0-M1 GPU/image feasibility** | `preflight`, backend adapters, profile/attribution. Verify existing environments, full text offload, strict image loading, device execution, conditional/causal checks and ordinary full canvas. Output GPU evidence, selected checkpoint/hash/terms, generation/replay/load timings. | About 1 day; at most 3 for image problems. Missing GPU/checkpoint/terms, incorrect PMFs or projected excess cost stops bidirectional feasibility. Defer extra backends, repair frameworks and training. |
| **V0-M2 Packet and first text recovery** | Depends on M1 text gate; `packet`, `fixed_rank`, text sender/receiver, focused tests. CPU golden tests first; then one GPU-encoded saved text, fresh receiver and evaluator equality with source image. Output packet vectors and retained example. | 0.75–1.25 days; token consistency/replay risk. Stop integration on framing defects, insufficient support or divergent replay; no saved-ID/CPU fallback. Defer other coders and full static-mask comparison. |
| **V0-M3 First PNG recovery** | Depends on M1 image gate/M2 packet. Connect discrete PMFs, row context, full PNG completion and independent receiver. Recover one authenticated text exactly, verify PNG samples and GPU replay evidence. | 0.75–1.25 days; posterior/device/causality risk. Stop on incorrect distribution, changed pixels or recovery failure. Shares M1's total image-problem time box; defer optimizations and extra contexts. |
| **V0-M4 Ten-case demonstration** | Depends on M2/M3; `demo`, evaluator, usage docs. Preselect manifest; run ten cases serially across fresh processes, retain keys/carriers/results and verify receiver inputs/imports. Document working commands and measured cost. | 0.5–1.5 days, targeting 3–5 days total when compatible assets exist. Any failed case or missing GPU evidence prevents V0 acceptance; retain cause, do not substitute cases. Defer study infrastructure. |

M2's CPU work need not await all image investigation, but unresolved M1 image feasibility cannot be bypassed to declare V0 complete.

V0 acceptance requires **10/10 exactly recovered payloads** from delivered artifacts; both neural backends observed on GPU; compatible pinned sender/receiver configurations; authentication/strict parsing; separate source-byte/dimension comparison; permitted receiver inputs only; independent commands working after sender exit; every carrier and failure retained. Authentication alone is not equality.

Focused tests, without research infrastructure:

| Level | Independent evidence |
| --- | --- |
| CPU unit | All 256 bytes against handwritten high/low-nibble vectors; exact packet field offsets/size; bounds, malformed authenticated headers/padding; published AES-GCM vectors, wrong key/AAD/tampering; injected duplicate nonce and old-run refusal |
| Synthetic probability/tokenizer | Ties and zero mass; matched symbol ordering; 15-symbol support/exhausted capacity; UTF-8 split bytes, emoji/combining marks, whitespace, literal special strings, empty tokens, cross-token merges and tail-boundary consistency |
| Pixel unit | Independent high-precision scalar CDF oracle including tails/tiny scales; small-alphabet joint-mixture enumeration detecting missing posterior updates; float64 PMF sums within `1e-12` |
| GPU integration | Actual allocation/execution, reset/incremental replay equality, future-pixel perturbation invariance, PNG sample equality, saved-file decoding without sender memory/diagnostics, evaluator source equality |

## 7. V1: methods and full development

**V1-M5 Methods/development pilot** follows V0; approximately 7–8 researcher-days. Add only `entropy_coding.py`, `arithmetic_coding.py`, necessary study-runner functionality and tests. It produces all-method artifact recoveries, calibrated profiles, dataset manifests and a measured freeze recommendation. Unresolved coder correctness or budget blocks V2.

Entropy uses `H=−Σq log2 q` over the complete eligible distribution and strict `H>τ`. Adapt RankCloak `revision_v3_entropy.py::{shannon_entropy_bits,entropy_eligible,generate_entropy_gated_span,calibrate_entropy_gate_thresholds}`; replace its inclusive comparison/top-p/saved-ID assumptions. Freeze each modality's median from ordinary development traces, serialized float64. Skips consume no bits but update context and obey identical filtering; pending rank packets still require 16 eligible symbols. Test below/equal/above threshold and permanent skips.

The mandatory comparator is [Ziegler, Deng and Rush](https://aclanthology.org/D19-1115/), with inspected [reference arithmetic.py](https://github.com/harvardnlp/NeuralSteganography/blob/14e982564aeaf9a33f7b4de440deda2184d17f12/arithmetic.py) at `14e982564aeaf9a33f7b4de440deda2184d17f12`, `encode_arithmetic`/`decode_arithmetic`. No license was identified there: independently implement the published algorithm with attribution unless copying permission is established.

Retain proposed amendment **A1**, now V1-only: replace the reference's final-token endpoint dump with common-prefix stopping at 2,336 bits. Use 32-bit integer half-open intervals. Partition in frozen probability/ID order. At width R, retain q≥1/R plus at least the top min(2,support,R); renormalize, round widths nearest/even, truncate before the first cumulative overflow, assign residual to first symbol, remove zero widths. Require positive bins summing to R. Select using the next 32 packet bits, zero-extended; emit common leading bits of lower and upper−1, shift bounds accordingly. Stop at the first emission reaching 2,336; verify/discard at most 31 emitted zero suffix bits. No EOF token, final-artifact shortcut or flush during completion. Zero-bit steps consume capacity; nontermination fails explicitly. Record quantization loss, lookahead and suffix overhead. Verify with a separately written rational/bitstream oracle, enumerated finite messages, changing distributions, exact boundaries and truncation before model integration. This is a framed comparator adaptation, not a new invention or bit-identical reproduction.

Complete the methodological static-mask versus sequence-check comparison: 20 development images × two prompts = 40 pairs/80 artifacts, requiring all 40 sequence-check fixed-rank recoveries before main work. Both arms differ only in singleton versus complete-prefix filtering. Add fixed-image checks over 20 texts × two rows and all-method timing cases; no test-set tuning.

Dataset proposals: 20 development payloads/direction include the five V0 fixtures plus 15 additional sources; image additions from Fashion-MNIST training data, text additions from Gutenberg 11/84, ten texts per length band overall. The amended held-out allocation uses 20 distinct Fashion-MNIST test images, two/class, and 20 unchanged nonoverlapping Gutenberg 1342/1661 spans, ten per 32–64/65–128-byte band. Preserve the proposed source corpora, selection rules and exclusions; do not select easier examples using pilot failures. Pin grayscale BOX resize 28→16 and byte/codepoint-boundary selection; exclude boilerplate and duplicate source/canonical bytes across splits before generation. Record archive/version/URL, terms, hashes, indices/offsets, preprocessing and exclusions. Preserve [Fashion-MNIST licensing](https://github.com/zalandoresearch/fashion-mnist/blob/master/LICENSE) and [Gutenberg conditions](https://www.gutenberg.org/policy/license.html); corpus suitability remains a V1 decision.

Freeze the second prompt, “Explain how a home cook prepares a simple vegetable soup. Use continuous prose.”, and a second independently drawn row before payload generation. Seed allocation uses a fixed allocation seed plus split/direction/payload/context/purpose, with one independent main-control seed per payload/context group, shared across its methods. Seeds never supply cryptographic randomness. Within a new study run, encrypt each payload/context packet once and pair that exact packet across all methods.

## 8. V2: frozen evaluation and auditable results

**V2-M6 Frozen evaluation**, approximately 5–6 days, requires V1 correctness, calibration, frozen configuration and measured budget. **V2-M7 Reproducibility/paper evidence**, approximately 10–11 days, follows reconciled results. Outputs are paired tables, failure accounting, grouped intervals, bounded detection, artifact examples, four methodological figures and claim-to-evidence records. No new methods or model-family sweeps. Combined planning envelope is approximately 25–30 researcher-days, not a guarantee.

Freeze 20 held-out payloads × one context × three methods × two directions = **120 stego units**. Use only the existing first prompt/row. Generate at most **40 independent ordinary traces**, one per payload/context group; reuse matched text prefixes/full PNG controls across its methods. There are 20 independent payload groups per direction, not 60, and a shared trace is not three independent controls. Ordinary controls use the same eligible distribution and realized text length/full visible canvas. Record missing controls when no carrier exists; do not regenerate for appearance. Shared/duplicate controls are linked, not counted as independent observations.

Extend V0's single append-only `results.jsonl` schema, not a reporting framework:

| Fields | V0 / later use |
| --- | --- |
| Case, direction, run/work/attempt ID, profile/model/runtime/device IDs, GPU-evidence/log references | Required V0 |
| Carrier/recovered paths and hashes, packet-complete/carrier-complete/authenticated/source-equal statuses, failure stage/reason | Required V0; evaluator alone supplies equality |
| Encode/decode and cold-load seconds, carrier bytes, delivered tokens or pixels/channels, packet-stop/completion counts | Required V0 |
| Source/packet bytes, skipped positions, framing/slot/alignment/termination overhead, control/scoring seconds, peak RSS/VRAM, model calls | V1/V2 expansion |
| Pair/group/context/method/seed, provenance, rank/surprisal/entropy/retained-mass diagnostics, control links, invalidation lineage | V1/V2; private references/diagnostics never receiver inputs |

Work IDs hash frozen configuration/split/direction/payload/context/method/replicate 0. V1 adds atomic terminal records, validated artifacts and minimal checkpoint/resume support if needed. Resume decoding/scoring existing artifacts; restart interrupted encoding in a new key/run namespace, retaining paired-method lineage. Protocol failures remain terminal observations, not opportunities to retry for success. Reconcile attempts without counting resumptions/duplicates twice. Code fixes invalidate affected work; aggregate one accepted code/design revision.

Do not build persistent prefix caches for V0. If V1 needs them, identity includes complete model/tokenizer/runtime/device/precision/source/config/context/prefix/stage hashes; changes invalidate descendants. Receivers never read sender caches. Freeze dependency/build locks, model/tokenizer SHA-256, source/diff hashes and sampling versions.

Report attempted, packet-completed, carrier-completed, authenticated and exact counts separately. Scheduled-but-unstarted work is not attempted; incomplete allocation is not a completed study. Give exact/attempted, exact/packet-completed and exact-and-carrier-complete rates. Useful rate is `8L/all delivered symbols`; transport is `2336/symbols through packet stop`, including skips/zero-bit steps. Keep bits/token, bits/channel and bits/pixel distinct. File expansion is serialized carrier bytes/L. Report conditional rates and failure-inclusive delivered goodput; no-artifact failures still consume attempted/time denominators. Undefined rates retain reasons.

Separate header/nonce/tag, slot padding, rank alignment, arithmetic termination, skips and completion. Compute likelihood/rank summaries over packet positions, packet span and whole carrier; fixed top16 distortion diagnostic is `−4−mean(log2 q_top16)`. Bounded detection uses whole-carrier mean surprisal and log-rank against controls, with no trained detector or packet-boundary leakage. Report AUC and unscorable counts. Use 2,000 payload-group bootstrap replicates for 95% paired intervals, retaining all contexts/methods/control dependencies; report group counts and boundary-rate intervals, not an unsupported 99.9% claim. Preselect 20 lossless PNG re-save/metadata-removal checks plus UTF-8 save/load checks; missing artifacts remain failures, not replacements.

## 9. Compute allocation and stopping

V0 receives a proposed **two GPU-hour initial cap**, charged within the existing 40, including preflight, ordinary image/row, preliminary examples, ten-case encoding, independent replay, model loading and failures. First measure one complete encode/replay per direction and cold loads. Count occupied GPU time during CPU filtering/bookkeeping; synchronized timings are essential. No throughput is assumed. Enforce the remaining allocation as a timeout; project initial-step costs before full-canvas runs.

For five cases/direction, conservatively project:

`G_V0 = 1.25 × [G_spent + Σ_remaining(t_load + t_encode + t_receiver_load + t_decode) + G_remaining_preflight/checks]`.

Use observed maxima/length-sensitive costs, including full PNG replay and text filtering. Preliminary examples already spent are not counted again; new ten-case runs are additional work. Require this estimate ≤2 hours before continuing the demonstration. If it cannot fit, stop and report measured costs and the needed within-ceiling reallocation; no automatic expansion or CPU substitution.

V1 initially reserves another two GPU-hours, making the initial development allocation four combined. Proposed full development work is 152 stego artifacts: 80 text filter-comparison artifacts + 40 fixed-image cases + 32 additional gated/arithmetic timing cases, with up to 48 timing controls and 16 ordinary calibration traces. Budget V0 artifacts additionally; reusing their development source payloads does not create independent observations. Remaining required development must enter the projection before spending beyond that allocation.

With one frozen main context per direction and measured per-stage GPU-hour costs:

`G_total = 1.25 × [G_development + Σ_direction,method 20(g_generation + g_receiver) + G_shared_controls + G_extra_scoring + G_loads_and_process_overhead + G_serialization_checks] ≤40`.

Separate generation, receiver, controls and scoring; avoid charging already-recorded replay scores twice, but include extra passes when needed. Include spent failures and planned remaining development; apply the 25% reserve once, not recursively to V0's reserved estimate. Project cap-length failures/deadlines, CPU wall time and researcher days too.

V1.1 explicitly supersedes the earlier context-only reduction: the proposed main allocation is now 120 stego units and at most 40 shared controls. Keep all 152 originally planned development units and calibration/control qualification requirements (crediting only qualifying pilot units); no diagnostic replay is an extra observation or credit against unrelated development. Separate recorded history, remaining qualification, main inference, fresh receiver loads/process overhead, controls and the existing 20 additional lossless PNG replays. Apply the 25% reserve once to the unreserved combined estimate, not to previously reserved projections. Treat unmeasured static-mask/second-context costs as assumptions. If the revised estimate fails, stop for a reviewed budget/schedule decision. No automatic cloud allocation, larger hardware scope, training, direction/comparator removal or easier test selection.

## 10. Critical review and unresolved decisions

The review moved arithmetic, entropy calibration, datasets, static-mask comparisons, isolation frameworks and resumable scheduling out of V0. Essential framing, prefix consistency, RGB posterior updates, completion accounting, fresh-process recovery and observed GPU replay remain prerequisites. Fresh-run keys remove the need for a durable nonce service in V0. No saved-ID/latent/source leakage route is permitted; AEAD is not a naturalness, robustness or steganographic-security claim.

| Unresolved decision | Impact / resolving milestone |
| --- | --- |
| Compatible local CUDA environments, full layer offload and deterministic replay | Existing libraries/hardware are not execution proof; V0-M1/M2 must establish pinned evidence or stop |
| Accessible image checkpoint, terms, strict architecture and correct GPU PMFs | Main feasibility dependency; V0-M1/M3, maximum three image-problem days |
| A1 finite-stream arithmetic adaptation/license route | Existing proposed amendment retained, deferred to V1-M5; mandatory independent termination evidence before V2 |
| Corpus snapshots, gate medians, second context and measured allocation | Development-only decisions; V1-M5 freeze, never choose using test results |

The cap/tail classification clarifies the existing rule without changing either limit. Choosing the PyTorch candidate first and simplifying run management change engineering order, not the scientific method. The sole V1.1 scientific amendment is the explicitly authorized prospective sample/context/control allocation; no coder amendment or protocol change is silently adopted. A1 has a documented width-three stagnation vector: zero-bit steps alone are not stagnation, and no universal finite-termination claim follows from finite-message tests. Diagnose existing failures without requiring a rerolled full-size arithmetic text success. Completing that diagnosis is not by itself full comparator qualification.

## 11. Independent-review checklist

| Methodological requirement → | Component → | Verification evidence → | Milestone |
| --- | --- | --- | --- |
| GPU inference in both directions | Preflight/backends | Actual layer/tensor placement, allocation, execution and replay logs | V0-M1–M3 |
| Fixed packet and bounded-byte bridge | Packet/fixed coder | Field/golden vectors, all-byte mapping, authentication/nonce tests | V0-M2 |
| Recovery from actual files only | Receiver/evaluator | Fresh-process inputs/import review, absent diagnostics, byte equality | V0-M2–M4 |
| UTF-8 complete-prefix consistency | Text backend | Boundary fixtures and ten-case subset; full 40-pair comparison later | V0-M2; V1-M5 |
| Discrete RGB/private row/PNG | Image backend | Independent conditional oracle, causal checks, unchanged pixels | V0-M1/M3 |
| Working bidirectional prototype | Demo/docs | Ten retained GPU artifacts, 10/10 exact recoveries | V0-M4 |
| Gating and external comparator | Later coders | Gate synchronization, calibrated medians, finite-stream oracle | V1-M5 |
| Fair frozen matrix and overhead | Study runner/evaluator | Pairing/failure ledger, controls, unit-correct rates, grouped intervals | V2-M6 |
| Six-week/40-GPU-hour limits | Timing ledger | Stage projections, reserve and explicit stopping decisions | V0-M1/M4; V1-M5 |
| Bounded claims and reproducibility | Analysis/release evidence | Full hashes/attribution, serialization checks, claim-to-evidence links | V2-M7 |
