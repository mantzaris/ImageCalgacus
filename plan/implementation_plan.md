# Implementation plan: exact text/image steganographic transport

Draft for independent review, 7 September 2026. Planning only; no implementation, installations, weight downloads or experiments were performed.

## 1. Authority and inspected starting point

The scientific specification is [crossmodal_steganography_focused_research_plan.md](crossmodal_steganography_focused_research_plan.md), at repository revision `993626f599ff677fc5f03d88a6f431aa43aca966`, SHA-256 `644fc5ab443cdf9d008192078d98e6803a40b720ab599e79cec4d326adf03878`. Preserve its directions, packet, three methods, allocations, artifact recovery endpoint, six-week effort budget and 40 GPU-hour ceiling. Details below are proposals unless labeled inspected evidence or reported research; amendments are marked.

Inspection found four tracked files: that specification, `LICENSE` (MIT, a.v.mantzaris, 2026), an effectively empty `.gitignore`, and `.gitignore~`. `notes/` is empty. There is no implementation plan, README, application, dependency declaration, tests, configuration, dataset or models here. No applicable `AGENTS.md` was found in the repository or ancestors. All modules below are new here; reserve `notes/` for implementation observations.

Sibling checkouts contain external code at the specification's cited revisions:

| Inspected source | Reuse or adaptation boundary |
| --- | --- |
| [RankCloak](https://github.com/mantzaris/llm-rankcloak/tree/ce853d42d6ba64065cb63c6bdfc0d825c62734cd), `ce853d42d6ba64065cb63c6bdfc0d825c62734cd` | `rankcloak/rank_codec.py`: adapt `encode_bytes_to_bounded_ranks`, `decode_bounded_ranks_to_bytes`, and stable ordering primitives. Replace metadata-dependent, permissive length handling with the fixed packet contract. |
| Same revision | `model_io.py`: adapt `load_llama_cpp_model`, `evaluate_context`, `get_last_logits`, and `detokenize_bytes`. Do not inherit `safe_detokenize` replacement decoding or implicit BOS conventions. `revision_protocol.py::build_round_trip_stable_mask` supplies the development baseline only; `Representation` includes source bytes and `decode_representation` must not enter the receiver. |
| Same revision | `revision_v3_entropy.py`: adapt `shannon_entropy_bits`, `entropy_eligible`, `generate_entropy_gated_span`, and `calibrate_entropy_gate_thresholds`; remove top-p sampling and saved-ID replay dependencies. `reproducibility.py::write_manifest` and `bootstrap_statistics.py::bootstrap_mean_ci` are starting points, requiring complete hashes and payload-group resampling. |
| [LlmStenoExplore](https://github.com/mantzaris/LlmStenoExplore/tree/b9f1650b4eb0b2261b0080f86d9b1d8fadedbc0b), `b9f1650b4eb0b2261b0080f86d9b1d8fadedbc0b` | `paper-empirical-explorations/carts_empirical_utils.py`: reference `first_mismatch_position`, `sorted_token_ids_from_logits`, and `write_run_manifest`. Do not adopt `text_to_payload_ids`, which prepends a space, or display replacement decoding. |

The [RankCloak V3 manuscript](https://github.com/mantzaris/llm-rankcloak/blob/ce853d42d6ba64065cb63c6bdfc0d825c62734cd/paperV3/scientific_reports/main3.tex) reports 6,480/6,480 primary saved-ID recoveries and 88/144 visible-text retokenization recoveries. These reported results do not establish this project's endpoint. [Calgacus v1](https://arxiv.org/html/2510.20075v1) transports source-token ranks and discusses cross-domain models. This study uses RankCloak's existing byte-to-bounded-rank bridge instead of regenerating source tokens. Entropy gating, arithmetic steganography and [stepwise tokenization verification](https://aclanthology.org/2025.emnlp-main.361/) are also prior methods.

Local evidence: Python 3.10.13; NVIDIA RTX 5000 Ada (32,760 MiB) and Quadro T2000 (4,096 MiB) visible to `nvidia-smi`; a 4,920,734,272-byte `../llm-rankcloak/models/llama3_8b/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf` exists. Identity, loading, replay and throughput remain unverified. No image checkpoint was identified in this repository or the inspected sibling model directories.

The first image candidate is [official PixelCNN++](https://github.com/openai/pixel-cnn/tree/bbc15688dd37934a12c2759cf2b34975e15901d9), revision `bbc15688dd37934a12c2759cf2b34975e15901d9`. Its README advertises a CIFAR-10 checkpoint; `pixel_cnn_pp/nn.py` uses legacy `tensorflow.contrib`. Published availability does not establish download accessibility, local availability, runtime compatibility, or experimental suitability. All four must be recorded separately at M3.

A single bounded fallback is [pclucas14/pixel-cnn-pp](https://github.com/pclucas14/pixel-cnn-pp/tree/7cb4436f062fda9b63ecc9e3b75d2c2dcb379931), revision `7cb4436f062fda9b63ecc9e3b75d2c2dcb379931`: `model.py::PixelCNN.forward`, `utils.py::discretized_mix_logistic_loss`, and its advertised pretrained weights. Its `license.md` contains a nonstandard restriction on selling copies despite its MIT heading. Preserve that text; do not relabel it ordinary MIT. Both require runtime adaptation.

Record upstream notices/licenses, citations, files/functions, revisions and adaptations in future `THIRD_PARTY.md`; check weight terms separately. Do not import sibling checkouts directly.

## 2. Small architecture and information boundaries

Use a root-level `imagecalgacus/` package. Module paths below are relative to it; `configs/`, `tests/` and packaging files are repository-level. Dependencies: NumPy, `cryptography`, Pillow; optional `llama-cpp-python` and selected image runtime; pytest, Matplotlib and scikit-learn for verification/analysis. Pin versions/builds after feasibility. A legacy image worker may need a separate environment.

| Proposed location | Responsibility and principal contract |
| --- | --- |
| `payloads.py`, `packet.py` | Canonical payload preparation; `seal(payload, key, nonce_store) -> bytes[292]`; `open_packet(packet, key) -> Payload` after authenticated validation. |
| `probabilities.py` | `Model.start(context)`; `Model.distribution() -> Distribution` from its observed prefix; `Model.observe(symbol)`. Distribution contains observable IDs, normalized probabilities, deterministic order, and retained-mass diagnostics. No payload argument. |
| `rank_coding.py`, `entropy_coding.py`, `arithmetic_coding.py` | Pure coder state machines consuming distributions and symbols/bits; report recovered-bit count and stopping state. Depend on neither modality backend nor evaluator. |
| `text_model.py`, `pixel_model.py` | Conditional distributions and reproducible model state; candidate consistency and discrete RGB likelihoods. |
| `artifacts.py`, `sender.py` | Strict UTF-8/PNG I/O; packet transport, completion, timing and diagnostics. |
| `receiver.py` | `receive(carrier, profile, context, key)` returns recovered bytes or failure, plus independently determined stop position, conformance flags and diagnostics. |
| `runner.py`, `evaluation.py` | Enumerate work, isolate processes, retain failures; separate evaluator joins references, computes equality, metrics and grouped comparisons. |
| `configs/`, `tests/`, `pyproject.toml` | Frozen profiles/allocations, verification fixtures, dependency and CLI declarations. |

Public protocol configuration contains model/tokenizer identities, precision, ordering, eligibility, packet size/AAD, dimensions, method, thresholds, budgets, and serialization rules. Shared conditioning contains exact prompt bytes or the 96-byte row; it is distinct from the random AES key. Neither conditioning complexity nor model secrecy establishes cryptographic strength.

Per-message transported contents are only nonce, ciphertext and tag; protected plaintext contains header, payload and slot padding. Sender diagnostics may contain token IDs, traces, packet identity and timings. Evaluator-only records contain source bytes, source digest, provenance, payload IDs and pairing. None is a receiver input.

Stage only `carrier.txt` or `carrier.png`, validated profile, context and key in an opaque restricted receiver input directory. Remove payload-bearing names/comments. Launch a fresh process with a filesystem allowlist: read-only package/runtime/model assets and inputs, private scratch/output, no network, sender/evaluator directories, caches, inherited descriptors or sensitive environment variables. Reject symlinks/unexpected inputs. Demonstrate denied reads of external sentinel files: directory separation alone is insufficient. Sandbox startup failed during planning; working isolation remains an M2 dependency. Only afterward may the evaluator compare receiver and sender traces.

## 3. Packet and cryptographic contract

Use unsigned big-endian fields, with no structure alignment:

| Plaintext offset | Width | Permitted value |
| --- | ---: | --- |
| 0 | 1 byte | Version `1` |
| 1 | 1 byte | Kind `1` = UTF-8; `2` = grayscale |
| 2 | 2 bytes | Actual length: text 32–128; image exactly 256 |
| 4 | 2 bytes | Width: text 0; image 16 |
| 6 | 2 bytes | Height: text 0; image 16 |
| 8 | 256 bytes | Payload followed by zero slot padding |

Image payloads are 16×16 row-major unsigned grayscale bytes without container/header; canonicalize before defining the reference. Text is literal strict UTF-8: no normalization, trimming, leading space, newline conversion or replacement. Validate length before encryption; after authentication validate kind against direction, length, dimensions, UTF-8 and all padding. Reject unknown fields and surplus/truncated packets; never allocate using unchecked dimensions.

AES-256-GCM uses a separately generated 32-byte random key, a 12-byte nonce and full 16-byte tag via the [standard AESGCM API](https://cryptography.io/en/latest/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM). Fix AAD to the exact bytes `ImageCalgacus/packet/v1` without newline; do not bind the coding method. Transport `nonce || ciphertext || tag`: `12 + (8 + 256) + 16 = 292` bytes, or 2,336 bits.

Generate nonces with the operating-system CSPRNG. Atomically reserve each `(key_id, nonce)` in a durable sender ledger before encryption; retry collisions, and never release reservations after crashes. Refuse packet creation if the ledger for an existing key is missing. Encryption keys and ledger are outside version control. Encrypt once per payload/context pairing and reuse that exact prepared packet across methods; retries reload it. A deliberate new packet needs a fresh nonce and recorded attempt lineage. Experimental seed generators must never generate cryptographic keys/nonces.

The receiver knows the 292-byte target before decoding; encrypted length creates no framing cycle. Authenticate before parsing/exposing plaintext. Wrong key/nonce/AAD/tag returns authentication failure without partial plaintext. AEAD does not establish carrier undetectability or edit robustness.

Framing is 36 bytes: 8 header + 12 nonce + 16 tag. Slot padding is `256 − L` bytes: 128–224 for text, zero for images. Radix 16 has no bit alignment padding. Arithmetic suffix bits and ordinary carrier completion are separate overhead categories.

## 4. Shared probabilities and three coders

Freeze backend/device, inference precision, thread/batch sizes, deterministic kernels and reset/replay schedule. Disable dropout and stochastic model operations. Convert outputs to float64 for stable log-sum-exp normalization. Reject NaNs, positive infinities, empty support and invalid normalization; negative infinity denotes zero mass. Remove numerical zero probabilities, record their log-mass/count, then renormalize. Sum in ascending symbol-ID order; sort by decreasing resulting probability, then ascending symbol ID. No epsilon floors, temperature scaling, or nucleus truncation. Pin the sampler to NumPy PCG64 and inverse-CDF sampling in symbol-ID order at temperature 1. Receiver replay never needs its seed: observed symbols determine state.

Fixed rank maps each byte's high then low nibble `d` to one-based rank `d+1`, among the top 16 eligible symbols. Thus `292 × 2 = 584` packet-bearing positions. Decode exactly 584 valid ranks; reject 0, 17, odd counts and missing/excess ranks. A receiver cannot rely on the original codec metadata.

For gating, compute `H = −Σ q log2(q)` over the entire normalized eligible distribution before observing the next symbol. Use strict `H > τ`, resolving the specification's word “exceeds”; the prior inclusive `>=` helper requires adaptation. Calibrate each modality's median separately from ordinary development traces, using a frozen linear median convention and serialized float64 threshold. Skips sample from `q`, consume no bits, and still update context. While a rank packet is pending, fewer than 16 eligible symbols is a support failure even at a gated skip. Completion needs nonempty support; arithmetic needs whatever its integer partition can represent. Never widen the inspected candidate pool to rescue an attempt.

The comparator is the arithmetic interval method of [Ziegler, Deng and Rush](https://aclanthology.org/D19-1115/). Inspectable reference: [arithmetic.py](https://github.com/harvardnlp/NeuralSteganography/blob/14e982564aeaf9a33f7b4de440deda2184d17f12/arithmetic.py), revision `14e982564aeaf9a33f7b4de440deda2184d17f12`, functions `encode_arithmetic` and `decode_arithmetic`. No license file was present in its inspected tree: use an independently written implementation of the published algorithm with attribution, not copied source absent permission. Remove GPT-specific token repair and sentence finishing.

**Proposed amendment A1 — finite arithmetic framing.** The reference decoder emits an entire interval endpoint on its last token. Carrier completion makes that shortcut unsuitable. Instead both sides stop when common-prefix emissions reach 2,336 bits, using the reference encoder's zero-extension convention and the following explicit finite-precision profile:

- Precision 32; half-open interval `[0, 2^32)` with Python integer endpoints. At width `R`, retain probabilities at least `1/R`, keeping at least the top `min(2, support, R)` symbols. Renormalize retained mass to `R`, round nearest/even, truncate at the first cumulative overflow, assign remaining units to the first symbol, and remove zero-width bins. Assert positive widths summing exactly to `R`; record additional probability loss.
- Interpret the next 32 packet bits, extended with zeros, as a big-endian interval index. Select its bin. Emit only common leading bits of the lower endpoint and upper endpoint minus one. Remove those bits, append zeros to the lower endpoint and ones to the inclusive upper endpoint, then restore the exclusive upper bound. Both sides advance the bit cursor by emitted bits only.
- Stop on the first symbol bringing emitted bits to at least 2,336; check and discard any emitted suffix beyond that length, which must be zero and is at most 31 bits. Log zero lookahead separately from emitted suffix overhead. There is no EOF token, last-artifact-token shortcut, or flush during ordinary completion. Zero-bit steps count toward the cap; nontermination is capacity failure. Before packet stop, an observed symbol outside the eligible set or positive-width bins is decoding failure.

This is a framed adaptation of the external method, with 32-bit precision and bounded-support edge handling, not a new coding method or bit-identical reproduction. M4 must independently validate the interval updates and termination before comparison.

## 5. Text artifact contract

Use the existing Llama 3 8B Q4_K_M candidate with its embedded tokenizer. Define `T(bytes)` with explicit `add_bos=False, special=False`, and `D(ids)` as exact detokenization bytes without special-token rendering or text cleanup. Require backend support for those flags; compatibility fallbacks cannot silently change semantics. Prompt context is exactly one model BOS followed by `T(prompt_bytes)`, no chat template or EOS. The carrier is tokenized separately; replay concatenates prompt IDs and reconstructed carrier IDs, never tokenizes their joined strings. Start with batch/microbatch size 1 and `n_ctx=4096`; verify prompt length + 2,048 fits. Freeze offload/kernels after replay checks; no context-window sliding.

For every carrier prefix `s`, inspect the highest 256 model IDs before filtering, using stable ordering. Reject BOS/EOS/control/special IDs, empty byte renderings, non-strict UTF-8, and candidates failing `T(D(s+[v])) == s+[v]`. No extra prose-safety blacklist in the main condition. Apply this complete-prefix rule to packet positions, gated skips, arithmetic steps and all completion tokens. Serialize the final complete detokenization as binary-written UTF-8, without BOM or newline insertion. Receiver reads exact bytes, checks `D(T(file)) == file`, reconstructs every prefix and repeats eligibility/replay from scratch.

**Proposed clarification A2 — cap versus tail boundary.** Keep the 2,048-token total cap and exactly 32 completion tokens. Do not truncate unfinished packets to reserve a tail. A packet finishing after position 2,016 produces `packet_complete=true`, `carrier_complete=false`, `completion_budget` failure; neither extend the cap nor call a shorter tail complete. Preserve the separate recovery endpoint: the receiver still returns authenticated, parser-valid bytes if recoverable, with tail/eligibility conformance reported separately. Evaluate equality even for these incomplete carriers; do not redefine recovery as successful completion.

Completed fixed-rank text has `584+32=616` tokens and `(256×8)/616≈3.325` useful bits/token. These are calculations, not measurements. Retain failed prefixes, including completion failures. Receiver validates the entire sequence and reports whether exactly 32 eligible tokens follow its independently determined packet stop.

## 6. Pixel artifact contract and feasibility gate

Native canvas is height 32, width 32, three uint8 channels. Pre-share one 96-byte first row; generate rows 1–31, left-to-right, R then G then B. Deliver height 31, width 32 RGB PNG: 992 pixels, 2,976 channel values. Receiver reconstructs symbols from those pixels and prepends the shared row internally. Neither latents nor a PNG metadata channel is permitted.

For PixelCNN++, unpack mixture logits, means, log-scales clamped at −7, and tanh coefficients as in [`discretized_mix_logistic_loss`](https://github.com/openai/pixel-cnn/blob/bbc15688dd37934a12c2759cf2b34975e15901d9/pixel_cnn_pp/nn.py). For byte `v`, use `x(v)=2v/255−1` and half-bin width `1/255`. Interior component mass is the logistic CDF difference at bin edges; byte 0 includes the entire left tail and byte 255 the entire right tail. Compute stable log-CDF differences, not component-mean ranks or independently sampled continuous RGB.

Let `w_k` be softmax mixture weights and `f_Rk`, `f_Gk`, `f_Bk` component channel masses; normalize posterior weights after each update:

`q_R(r)=Σw_k f_Rk(r)`; `w_k^R ∝ w_k f_Rk(r)`.

`μ_Gk'=μ_Gk+c_RG,k x(r)`; `q_G(g|r)=Σw_k^R f_Gk(g; μ_Gk')`.

`w_k^RG ∝ w_k^R f_Gk(g; μ_Gk')`; `μ_Bk'=μ_Bk+c_RB,k x(r)+c_GB,k x(g)`; `q_B(b|r,g)=Σw_k^RG f_Bk(b; μ_Bk')`.

Posterior updates are required even though the network outputs are cached within a pixel. Validate the product of these conditionals against independently calculated joint mixture mass. The reference likelihood has a low-mass density approximation; the proposed adapter evaluates actual discretized CDF masses and measures approximation differences. This numerical specialization must be frozen and documented; do not claim exact reproduction of that training-loss approximation.

Use one network evaluation per visible pixel and identical serial sender/replay. Initialize unknown uint8 samples to zero before scaling. Prove current/future pixel values cannot affect current mixture parameters before caching within a pixel. Strictly load all inference tensors, including required EMA parameters; reject missing/unexpected tensors and partial loading. Ports, weight conversions, causal caches and TensorFlow/CUDA repairs threaten the three-day time box across both candidates; then stop without training or changing directions.

After the packet stop, sample every remaining channel from its appropriate conditional distribution, including the remainder of a partially used pixel. Fixed rank leaves `2,976−584=2,392` completion channels. Useful rate for 128 bytes is `1,024/992≈1.032` bits/pixel, or `1,024/2,976≈0.344` bits/channel. An unfinished packet at the visible boundary fails.

Pillow writes lossless 8-bit truecolor PNG, no palette, alpha, color conversion, packet metadata or trailing data. Receiver requires these dimensions/mode and reads samples without applying gamma/ICC transformations. Do not silently convert unsuitable input modes. Record file SHA-256 and pixel-array SHA-256 separately; PNG compression may change file bytes while preserving recovery.

## 7. Ordered implementation milestones

Effort estimates total 29–30 working days for one researcher; elapsed GPU time is separately budgeted. Later work cannot bypass failed gates.

| ID / objective | Dependencies; likely files | Concrete tasks and observable acceptance/output | Effort; principal risk / stop |
| --- | --- | --- | --- |
| **M1 Packet and CPU coder foundation** | Reviewed plan; `payloads.py`, `packet.py`, `probabilities.py`, three coder modules, `tests/`, `pyproject.toml`, `THIRD_PARTY.md` | Adapt bounded primitives; implement packet/nonce interfaces and synthetic arithmetic/gate fixtures. Produce golden vectors, license inventory and CPU report. All byte values invert; malformed packets fail; arithmetic fixtures recover or terminate as expected bounded failures. | 3 days; stop model integration if framing/inversion is unresolved. |
| **M2 Independent text recovery** | M1; `text_model.py`, `artifacts.py`, `sender.py`, `receiver.py`, isolation launcher/config | Pin local GGUF/tokenizer; implement complete-prefix filtering, prompt separation and 32-token completion. Run static-mask versus sequence-check comparison on 20 development images × two prompts: 40 pairs, 80 artifacts. All 40 sequence-check fixed-rank artifacts must recover exactly through restricted receiver inputs. Produce mismatch/support/candidate-cost report and denied-access isolation evidence. | 3 days; support, tokenizer throughput and process isolation may block. No saved-ID fallback. |
| **M3 Usable image backend** | M1 and receiver harness from M2; `pixel_model.py`, PNG integration tests, backend lock | Resolve checkpoint provenance/terms; strictly load it, verify channel PMFs/causality, and recover two development texts × two rows from four completed PNGs. Measure full-canvas generation and replay. Produce checkpoint manifest, numerical fixtures and artifact evidence. | 3 days maximum; stop after unresolved checkpoint/runtime problems; no replacement training. |
| **M4 All three methods on both artifacts** | M2–M3; coder adapters, calibration configuration/tests | Complete gated/artifact and arithmetic/artifact integration; calibrate ordinary-trace medians; demonstrate each method on each modality/context with known finite stopping. Retain support and capacity failures. Produce termination vectors, gate synchronization traces and comparator adaptation record. | 4 days; any implementation defect blocks M5. Functioning capacity failures remain outcomes. |
| **M5 Development pilot and freeze** | M4; `runner.py`, `evaluation.py`, `configs/development.json`, `configs/main.json`, payload manifests | Execute the bounded pilot below; test interruption/resumption and denied cache access; freeze payloads, contexts, seeds, thresholds, numeric rules, deadlines and hashes. Produce frozen work ledger, full cost projection and signed-off amendment decisions. | 3 days; no main run unless estimate fits both compute and researcher budgets. |
| **M6 Main comparison and analysis** | M5; runner, evaluator, result schemas | Execute exactly the frozen matrix, retaining all terminal outcomes; independently recover artifacts, generate controls, score and aggregate by payload group. Reconcile scheduled/attempted/completed/recovered counts and compute ledger. Produce paired tables, intervals, bounded AUCs and four specified figures. | 5 days; bugs invalidate affected work rather than select successful retries. |
| **M7 Reproducibility and reporting** | M6; release/manuscript documentation and analysis outputs | Reproduce summaries from immutable results; perform the preselected 20-case serialization checks; connect every claim to artifacts/tests, preserve attributions, and document limitations/compute. Produce reviewable release manifest and manuscript evidence tables. | 8–9 days; no new methods, training or model sweeps. |

M2's baseline adapts the isolated-token mask to the new tokenizer flags, without its optional prose blacklist. Both arms share packet, top-256 pool, special-token exclusions, sampler and budgets; only singleton versus complete-prefix consistency differs at every phase. M6's four figures cover architecture/inputs, recovery/failures, rate/distortion/runtime, and representative artifacts. M7 supplies a conditional correctness argument: reconstructible prefixes and identical distributions imply identical rank/gate/interval states; sufficient capacity and finite termination yield the framed packet.

## 8. Verification with independent checks

| Level | Required evidence |
| --- | --- |
| CPU unit tests, M1/M4 | Exhaust all 256 byte values against handwritten nibble formulas and fixed vectors, not only roundtrips. Test 291/292/293-byte packets, all parser fields and slot boundaries, authenticated invalid headers/padding, published AES-GCM vectors, wrong keys/AAD and tampering. Inject nonce collisions and crashes around reservation/encryption. |
| Synthetic coder tests, M1/M4 | Enumerate short bitstrings over uniform binary/16-way distributions; use a separate rational interval oracle for nonuniform and changing distributions. Include ties, zero mass, single-symbol support, exact interval boundaries, zero-bit steps, final zero extension and truncated streams. Force 15-symbol rank support, permanent gate skips and capacity exhaustion. Compare sender/receiver ordering and gate decisions at below/equal/above threshold. |
| Text integration, M2 | UTF-8 splits, combining characters, emoji, leading/trailing whitespace, literal special-token strings, empty token renderings and token merges across boundaries. Demonstrate a concatenation failure missed by isolated-token tests. Check every complete prefix, including skip/tail boundaries, and byte equality after raw save/load. Wrong context and malformed UTF-8 must fail without repair. |
| Pixel unit/integration, M3 | Independent high-precision scalar CDF calculations at 0/255 and tiny scales; enumerate a small RGB alphabet's joint mixture and marginals to expose missing posterior updates. Full 256-value normalization within `1e-12` in float64; inspect boundary rankings, causal masking and serial replay equality. PNG save/load must preserve every uint8 sample. |
| Development versus final | Development establishes feasibility/calibration and fixes software. Final evaluation uses frozen held-out payloads without tuning. Every claimed exact recovery requires a separate receiver's authenticated, parser-valid output and evaluator byte-for-byte equality with the canonical reference, including dimensions. Authentication alone is never source equality. |

Failures carry stage, reason, position and observed state. The evaluator adds the first divergent symbol only after replay; it never supplies that information to the receiver. Failure classes include serialization, unsupported input, support, numerical, capacity, completion-budget, timeout, authentication, parser, equality and infrastructure failures.

## 9. Executable experiment and result records

The methodology leaves corpus identities open. Proposed image source is [Fashion-MNIST](https://github.com/zalandoresearch/fashion-mnist), whose published [MIT notice](https://github.com/zalandoresearch/fashion-mnist/blob/master/LICENSE) must accompany reused data. Select 100 distinct official test images, ten per class; development has 16 official training images plus four synthetic patterns. Resize grayscale 28×28 to 16×16 using pinned Pillow BOX resampling; define references from the resulting uint8 bytes. Exclude duplicate source/canonical bytes across splits before freeze, deterministically taking the next candidate. This limits image claims to small clothing thumbnails.

Proposed text corpus: Gutenberg development excerpts from [11](https://www.gutenberg.org/ebooks/11) and [84](https://www.gutenberg.org/ebooks/84), held-out excerpts from [1342](https://www.gutenberg.org/ebooks/1342) and [1661](https://www.gutenberg.org/ebooks/1661). Retain copyright/license records and [distribution conditions](https://www.gutenberg.org/policy/license.html). Select unchanged, nonoverlapping UTF-8 body spans at word/codepoint boundaries; exclude boilerplate and duplicate bytes across splits. Development: 16 spans plus four Unicode fixtures, ten/size band. Test: 50 spans of 32–64 bytes and 50 of 65–128, balanced across works. M5 freezes selector/snapshots and verifies sufficient candidates without generation-based exclusions. Intervals describe payload pools, not independent books or universal language reliability.

Record source URL/version, license/hash, retrieval date, archive hash, index/byte offsets, preprocessing version, exclusions, canonical hash, split and size band. Select in seeded hash order (`20260907`). Reference manifests remain evaluator-only.

Freeze two prompt contexts: “Write a calm field-journal entry about a walk through a temperate forest. Use continuous prose.” and “Explain how a home cook prepares a simple vegetable soup. Use continuous prose.” The quoted contents, without quote marks, are exact UTF-8 prompt bytes. Draw two prefix rows from ordinary unconditional PixelCNN++ sampling with independent context seeds; freeze the resulting 96-byte rows before payload generation. No payload-dependent conditioning or prefix selection by appearance.

Test allocation: `100 payloads × 2 contexts × 3 methods × 2 directions = 1,200` stego units; at most 1,200 controls. Pair packet/context across methods. Derive PCG64 seeds from the first 128 SHA-256 bits of allocation-seed/split/direction/payload/context/purpose; include method for controls and trace index for calibration/row draws. Coupled sender seeds need not produce identical paths.

Controls sample the same eligible distributions at realized text length or visible image dimensions. Preallocate one slot/work unit; record omissions when no carrier exists. Never regenerate for appearance. Deduplicate exact controls for detection; cluster all identical carriers together when resampling, reporting distinct counts. Incomplete pixel prefixes remain diagnostics, not zero-filled PNG carriers.

Stable work ID hashes frozen configuration, split, direction, payload ID, context ID, method and replicate `0`. Substage IDs identify send/receive/control/score. Atomically record started/completed/failure status, immutable artifact hashes and attempt lineage. Resume verifies outputs and skips verified terminal work; restart interrupted generation from its prepared packet/seed, counting all incurred cost. Infrastructure retries share one statistical work unit; protocol failures are terminal. Code fixes invalidate affected work with retained lineage. Aggregate one accepted revision/design tuple, never pooled retries.

Cache keys cover full model/tokenizer SHA-256, runtime/build/device/precision, source revision, profile hash, context hash, complete symbol prefix and stage. A changed dependency invalidates descendants. Sender caches remain private; receiver initializes independently and may cache only its own replay. Record full dependency lock hashes, dirty-tree diff hash, configuration canonical hash, sampling algorithm/version and source/data hashes; do not use filenames as identity.

Proposed CLI: `python -m imagecalgacus.runner STAGE --config configs/main.json --resume`, with stages prepare/send/receive/control/score/aggregate. Minimal append-only records:

| Record | Required fields |
| --- | --- |
| `work_units.jsonl` | IDs/pair/group, allocation, method/context/seed, packet ID (sender/evaluator only), lineage, statuses, failure stage/position, `packet_complete`, `carrier_complete`, `authenticated`, `source_equal`; artifact/reference/output hashes in their permitted stores. |
| `measurements.jsonl` | Source/packet/file bytes; tokens or pixels/channels; packet-stop position; forced/skipped/completion counts; framing/slot-padding bits; arithmetic emitted suffix and lookahead; encode/decode/control/score and cold-load seconds; CPU/GPU seconds, peak RSS/VRAM, model forward calls and distribution-query counts. |
| `traces.jsonl` | Position/role, raw/eligible log probabilities and ranks, entropy, support, truncation/filter/quantization mass, emitted bits; receiver-generated traces stay separate until evaluator joins. |
| `controls.jsonl`, summaries | Control associations/dedup groups, score availability, denominator counts, aggregation configuration, paired differences and bootstrap seed. |

Report attempted, packet-completed, carrier-completed, authenticated and exactly recovered counts separately. Primary exact/attempted requires authenticated source equality; also give exact/packet-completed and the joint exact-and-carrier-complete rate. Unstarted scheduled work is separate; an incomplete matrix is not a completed study.

Useful rate is `8L / total delivered tokens` or `8L / total pixels`; additionally report image bits/channel. Transport rate is `2,336 / symbols through packet stop`, including skips and arithmetic zero-bit steps. Expansion is actual UTF-8/PNG bytes divided by `L`. Report conditional completed-artifact rates plus failure-inclusive delivered goodput, `Σ(exact × 8L)/Σ delivered symbols`; retain costs of no-artifact failures in time-based goodput. Undefined transport rates remain missing with reasons, never successful zeros. Pre-shared row cost is 96 bytes/context, separate from transmitted rate.

Aggregate surprisal/ranks over packet-bearing positions, packet spans and whole carriers, with corresponding control boundaries. Include retained mass and uniform-top16 diagnostic `−4−Σ(log2 q_top16)/16`, not an assumption of perfectly uniform finite packet bits. Detection uses whole-carrier mean surprisal and mean log-rank, higher meaning stego, without key/packet boundaries; report AUC unchanged even below 0.5 and unscorable counts. Bootstrap 2,000 payload groups for 95% intervals, preserving methods, contexts, strata and shared-control dependencies. Report effective cluster counts; for boundary recovery rates add Wilson intervals on groups recovering under all contexts. Report paired differences, joint-valid counts and failure-inclusive counterparts; repeated contexts are not independent payloads.

## 10. Pilot, compute projection and stopping rules

Allocate four GPU-hours initially. Start with two artifacts/modality. Text comparison contributes 80; image fixed-rank checks use all 20 development texts × two rows = 40, including M3's four feasibility cases. Timing uses four preselected payloads/direction × two contexts × three methods = 48, reusing 16 fixed-rank cases: 152 unique development stego artifacts. Include both text-length bands/Unicode; M4 demonstrations are included, reruns charged. Add at most 48 timing controls, 16 ordinary calibration traces (four/context/modality) and four unfiltered text traces. Generate rows once; no held-out calibration.

Measure loading, context initialization, full encode, independent replay, controls, scoring, prefix-length-dependent filtering CPU cost, model calls, memory and failures. Calibration targets 616-token text traces and full image canvases; pool valid ordinary positions per modality and report failed traces. Do not assume 50% gate acceptance on stego paths. Freeze per-stage/modality deadlines covering the slowest method's projected cap cost; timeouts are terminal.

For each direction/method, estimate conservative per-attempt stage costs from pilot lengths/calls and the maximum observed stage cost; also project cap-length failures. With `C` contexts, `N_dm=100C`:

`G_projected = 1.25 × [G_dev + Σ_dm N_dm(g_send,dm + g_receive,dm + g_control,dm + g_score,dm) + G_load + G_serialization_checks] ≤ 40 GPU-hours`.

Here each `g` is measured GPU time, including occupied GPU time during CPU filtering; `G_dev` includes spent and remaining required development. Avoid double-counting scores computed during independent replay, but include separate control scoring and any needed extra pass. Preselect 20 image work IDs across methods before outcomes; re-save with different lossless compression, strip ancillary metadata, verify pixel equality and replay. Do not replace missing carriers. Include raw UTF-8 byte checks. Sum device-hours if multiple GPUs are used. Project CPU wall time and researcher effort separately; hardware visibility is not a scheduling reservation.

The 25% multiplier reserves failures and required reruns; no throughput is assumed. Stop at the pilot ceiling if required checks/projection cannot be established. If the full estimate exceeds budget, the only permitted main reduction is the second context becoming development-only: 600 stego units, at most 600 controls, still 100 test payloads/direction and all three methods. Freeze that choice before test generation. If this also fails, pause for a reviewed schedule/budget amendment; do not drop directions/comparator, train models, select easier payloads or broaden hardware scope automatically.

## 11. Critical review and unresolved decisions

Review resolved receiver/reference coupling, framing, arithmetic stopping, complete-prefix checks, RGB posteriors and recovery/completion conflation. It checked padding, pairing, failures and development-only calibration. No steganographic security, naturalness, inherited-method novelty, cross-device recovery or unmeasured feasibility is claimed. Latent, overlay, high-resolution, training and model-family work remain deferred.

| Unresolved decision | Impact and required resolution |
| --- | --- |
| A1 arithmetic framing/precision adaptation and source licensing route | Review the stated departure from the reference EOF shortcut; use paper-based code unless copying permission exists. M1/M4 must provide independent finite-stream vectors. Comparator remains mandatory. |
| A2 late packet completion classification | Review the proposed interpretation of cap plus exact tail; freeze statuses/endpoint before M2/M5. No cap or tail length change is proposed. |
| Image checkpoint/runtime/terms and exact CDF adapter | Published links remain unverified; strict loading, conditional checks and four PNG recoveries required by M3 within three days. Numerical approximation differences must be recorded. |
| Isolation and deterministic backend | Denied-access checks and independent identical ordering required at M2/M3; existing planning sandbox failure prevents assuming availability. |
| Corpus snapshots, medians, context rows and measured budget | These require development, not invented values. M5 must freeze manifests, thresholds, rows and one/two-context allocation; insufficient candidates or budget requires documented review before main work. |

Datasets, prompts, nonce handling and numerical conventions fill specification omissions. Review A1/A2 explicitly; packet size, questions, recovery source and all methods/directions remain fixed. The fallback remains PixelCNN++ under the same gate. Further methodology changes require amendments.

## 12. Independent-review checklist

| Methodological requirement → | Implementation component → | Verification evidence → | Milestone |
| --- | --- | --- | --- |
| Fixed 292-byte authenticated packet | `packet.py` | Golden vectors, parser bounds, nonce/crash tests | M1 |
| Existing bounded-byte bridge | `rank_coding.py` | All-byte independent inversion, strict 584-rank endpoint | M1 |
| Recovery solely from delivered artifacts | `receiver.py`, isolation launcher | Restricted-input listing, denied reads, evaluator equality | M2–M3 |
| Complete-prefix UTF-8 consistency | `text_model.py`, `artifacts.py` | 40-pair comparison; all 40 main-filter fixed recoveries | M2 |
| Observable RGB and private prefix | `pixel_model.py` | Joint/conditional oracle, causal checks, PNG equality/replay | M3 |
| Entropy gate and external comparator | gated/arithmetic coders | Frozen medians, synchronized gates, finite-stream vectors | M4 |
| Equal packet/context/budget allocation | frozen configs, `runner.py` | Work ledger, pairing/control links, resume/invalidation audit | M5 |
| Failure-inclusive rates and bounded detection | `evaluation.py` | Denominator reconciliation, overhead tables, grouped intervals | M6 |
| Six-week / 40 GPU-hour limits | pilot and compute ledger | Measured stage projection with 25% reserve and stop decisions | M5–M7 |
| Limited claims and reproducible release | reporting, attribution manifest | Claim-to-evidence links, 20-case serialization check, full hashes | M7 |
