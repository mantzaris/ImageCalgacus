**A focused research plan for Calgacus-inspired text/image steganography**

Repository-informed revision, 7 September 2026. Proposed study; no new model experiments were run in preparing this plan.

**1. The recommended contribution**

Develop and evaluate one shared packet protocol that carries small images through generated text and short text through generated images, with exact recovery from the delivered UTF-8 or PNG artifact. Compare the existing bounded-rank method, its existing entropy-gated variant, and an established arithmetic-coding steganography comparator.

The central question is: **How much usable capacity and distributional distortion remain when Calgacus-inspired rank transport must work through actual text and image files, including serialization, framing, and completion overhead?**

This makes the new work a focused extension of your existing empirical program. It does not require a new foundation model, a new cryptographic primitive, a general multimedia format, or a large detector-training project. A plausible working title is *Exact Text-Image Steganographic Transport with Autoregressive Rank Coding*.

Calgacus already proposes using different discrete autoregressive models and discusses different vocabulary sizes. Therefore, the general observation that rank transport can cross domains is prior work. Your bounded-byte bridge is also already implemented. The prospective contribution is the evaluated combination of artifact recovery, modality-specific constraints, and honest net-capacity accounting. Whether that supports a journal paper depends on the resulting evidence and the related-work comparison. [Calgacus](https://arxiv.org/html/2510.20075v1)

**2. What the repositories change**

I reviewed RankCloak at commit `ce853d42d6ba64065cb63c6bdfc0d825c62734cd` and LlmStenoExplore at `b9f1650b4eb0b2261b0080f86d9b1d8fadedbc0b`. The review covered relevant implementation modules, tests, configuration, the RankCloak V3 manuscript, and the Explore empirical notebook, utilities, and written results. Reported results below are repository findings, not an independent rerun.

| Existing evidence or implementation | Consequence for this study |
| --- | --- |
| RankCloak already converts arbitrary bytes into bounded ranks and back. | Use this directly for image pixels and UTF-8 bytes; no hexadecimal text wrapper or new byte-to-rank invention. |
| RankCloak reports 6,480/6,480 primary recoveries with saved token sequences, but 88/144 after visible-text retokenization in its robustness subset. | Make recovery from the delivered artifact the primary endpoint. Saved-ID replay becomes a diagnostic. |
| Entropy gating is implemented and evaluated; stricter gating increases length and can exhaust the generation budget. | Reuse one gate setting. Do not make another gate sweep the main contribution. |
| Segmentation, compact controls, lead-ins, and completion policies have already been explored. | Freeze one packet and one completion policy. Separate payload positions from nonpayload completion in every metric. |
| RankCloak already contains substantial neural steganalysis. | Keep detection exploratory here; avoid repeating the full detector benchmark. |
| Explore studies finite key collisions, candidate shrinkage, noncommutativity, and perturbation sensitivity. | Reuse reproducibility and diagnostic practices. Defer another key census or avalanche study. |

Sources: [RankCloak V3 manuscript](https://github.com/mantzaris/llm-rankcloak/blob/ce853d42d6ba64065cb63c6bdfc0d825c62734cd/paperV3/scientific_reports/main3.tex), [bounded-rank implementation](https://github.com/mantzaris/llm-rankcloak/blob/ce853d42d6ba64065cb63c6bdfc0d825c62734cd/rankcloak/rank_codec.py), [entropy implementation](https://github.com/mantzaris/llm-rankcloak/blob/ce853d42d6ba64065cb63c6bdfc0d825c62734cd/rankcloak/revision_v3_entropy.py), and [Explore empirical summary](https://github.com/mantzaris/LlmStenoExplore/blob/b9f1650b4eb0b2261b0080f86d9b1d8fadedbc0b/paper-empirical-explorations/results/text/empirical_summary.md).

**3. Scope and exact recovery contract**

Use one existing Llama 3 8B Q4_K_M setup from your work and one pretrained pixel-autoregressive image model. Pin model hashes, tokenizer, backend, precision, probability calculations, and serialization rules. This study establishes recovery within that fixed environment.

| Direction | Secret payload | Delivered carrier | Exactness criterion |
| --- | --- | --- | --- |
| Image to text | A canonical 16 x 16, 8-bit grayscale image: 256 pixel bytes | A UTF-8 text file | Every canonical source pixel is recovered exactly |
| Text to image | A valid UTF-8 message of 32-128 bytes | A small RGB PNG | Every original UTF-8 byte is recovered exactly |

Create the canonical image before defining it as the payload. Downsampling an original photograph to that image is preprocessing; recovery does not restore the original photograph or its original PNG/JPEG container bytes. Text receives no normalization, silently inserted leading space, or replacement decoding.

The receiver receives only the carrier, the pre-agreed profile, shared conditioning context, and cryptographic key. It receives no payload-specific JSON, saved token IDs, rank trace, padding count, source digest, or sender-side representation object. Run it in a separate process whose input directory contains only those allowed inputs. Keep the source digest in a separate evaluator.

Maintain three distinct results: packet embedding completed; packet recovered and authenticated from the artifact; recovered payload equals the evaluator's reference. Count timeouts, insufficient capacity, and decoding failures in the attempted-trial denominator.

**4. Resolve MIME and padding with a fixed packet**

For the first study, pre-agree a 256-byte payload slot for both directions. Encode an eight-byte header followed by that slot:

| Header field | Size | Meaning |
| --- | --- | --- |
| Protocol version | 1 byte | Frozen parser version |
| Payload kind | 1 byte | UTF-8 text or raw grayscale pixels |
| Actual payload length | 2 bytes | Number of meaningful bytes in the slot |
| Width | 2 bytes | Image width; zero for text |
| Height | 2 bytes | Image height; zero for text |

Fix byte order in the profile. Pad unused slot bytes with zeros. Encrypt and authenticate the complete 264-byte header-plus-slot using an existing AES-GCM implementation, a separately shared random key, and a unique 12-byte nonce. Carry the nonce and the resulting ciphertext/tag through the steganographic channel too. Bind the fixed packet-format version as associated data; the transport method is agreed separately, allowing the same prepared packet to be compared across methods. A 16-byte tag gives a total transported packet of **292 bytes**, or **2,336 bits**. The library primitive and its nonce requirements are established infrastructure. [AES-GCM API documentation](https://cryptography.io/en/latest/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM)

This small wrapper has several practical benefits. It prevents a constant plaintext header from producing the same forced carrier prefix under every reused prompt. It protects the type and length together with the payload, gives an unambiguous corruption check, and provides ciphertext-like inputs for all three coding methods. Its security is separate from whether the resulting carrier looks ordinary. Use a standard library without modifying the primitive.

The receiver knows the total 292-byte packet size in advance, so there is no circular need to decrypt a length before knowing where the packet ends. After authentication it reads the actual payload length, checks the dimensions/type, and discards slot padding.

There are three separate notions of padding:

| Layer | Treatment |
| --- | --- |
| Payload slot padding | Zero bytes inside the authenticated, encrypted packet; removed using the protected length |
| Rank-symbol alignment | None with radix 16: every byte maps to exactly two four-bit rank symbols |
| Carrier completion | Ordinary generated text or pixels after the packet; never interpreted as payload |

The arithmetic comparator may have its own finite-stream termination overhead; account for that separately. No full MIME string or custom padding research is necessary. The outer file is ordinary text or PNG, while the protected header identifies the inner payload. The image carrier contains no packet in PNG metadata or appended file bytes.

The fixed slot deliberately trades efficiency for a simpler first protocol. A 128-byte message uses 128 padding bytes; report that cost. Variable-size slots, compression, and hidden length buckets become later extensions if this cost proves important.

**5. Coding methods: three conditions only**

Use the same prepared packet for the paired coding methods. Prepare its ciphertext once, rather than encrypting different messages under a reused nonce. Retain a nonce uniqueness check across packet creation.

| Method | Rule | Purpose |
| --- | --- | --- |
| Fixed rank | Four packet bits select one of the 16 highest-ranked eligible symbols | Reuses the existing bounded-byte codec |
| Entropy-gated rank | Carry the same four bits only when conditional entropy exceeds a frozen median threshold; otherwise sample an ordinary symbol | Reuses RankCloak's existing adaptive mechanism |
| Arithmetic coding | Adapt an established finite-precision arithmetic steganographic coder to the same conditional distributions | Provides an external methodological comparator |

For the rank methods, convert a four-bit integer `d` into rank `d + 1`. Resolve probability ties by symbol ID, matching your existing deterministic ordering. The fixed method therefore needs **584 packet-bearing symbols**. For gated coding, sender and receiver calculate eligibility before consuming the next observed carrier symbol. Ineligible positions consume no packet bits. The known packet size provides the stopping condition.

Calibrate a separate median entropy threshold for each modality using ordinary development traces, then freeze it. A single numeric threshold shared across text and image models would not be a meaningful matched treatment. Define ordinary sampling as temperature 1 from the normalized eligible distribution, without additional nucleus truncation. Use that rule for gate skips, completion, and matched controls.

The arithmetic comparator should reuse a published approach, including its termination rules. Verify its integer probability quantization and finite-message inversion on synthetic distributions before connecting either model. All methods use the same carrier eligibility constraints, packet contents, context allocation, and output budgets. Measure any additional coder overhead and retained probability mass. Arithmetic coding is an established baseline, not a proposed novelty. [Neural Linguistic Steganography](https://aclanthology.org/D19-1115/)

**6. Image to text: fix the serialization problem first**

RankCloak's isolated-token stability mask is useful but does not establish stability of an entire concatenated text sequence. Start from a stepwise tokenization-consistency approach and adapt it to the fixed backend. This is known prior work and must be credited. [Yan and Murawaki, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.361/)

For a generated carrier-token prefix `s` and candidate token `v`, require strict UTF-8 decoding and:

`tokenize(detokenize(s + [v])) == s + [v]`.

The equality concerns the complete carrier prefix. Tokenize the shared prompt separately and concatenate its fixed token IDs with the recovered carrier IDs when replaying the model. Fix special-token and BOS behavior explicitly.

Bound candidate inspection to the top 256 model tokens before filtering, use deterministic ordering, and renormalize the retained probabilities. Apply the same rule during packet coding, skipped positions, and completion. If fewer than 16 candidates remain in a rank condition, record a support failure rather than silently changing the alphabet. Record the probability mass lost to candidate truncation and consistency filtering.

Use a 2,048-token total output cap. After packet completion, append exactly 32 ordinary sampled tokens under the same consistency rules. This freezes tail cost without adding another completion-policy experiment. Do not reserve 32 tokens by truncating an unfinished packet; classify that attempt as budget exhaustion.

First compare the existing static mask and the sequence check on 20 development image payloads under two prompts. Read back only the saved UTF-8 files. That 40-pair comparison isolates a concrete difference from your prior work, without rerunning its full benchmark. Require successful fixed-rank artifact recovery on this development set before scaling.

**7. Text to image: use observable pixels**

Select a pretrained PixelCNN++ implementation/checkpoint as the first candidate. It models pixel likelihoods and has published reference implementations; checkpoint availability, runtime compatibility, and suitability must pass the initial feasibility gate. Do not train a replacement model within the core study. [PixelCNN++ paper](https://arxiv.org/abs/1701.05517), [official implementation](https://github.com/openai/pixel-cnn)

Use 8-bit channel values as the observable alphabet. At each step, obtain the normalized conditional probabilities of values 0-255, rank those values, and apply the same packet coder. Generate in a fixed raster order with R, G, then B within each pixel. With PixelCNN++, derive the discrete channel probabilities from the mixture likelihood, including the within-pixel conditioning and mixture posterior updates. Ranking logistic-component means or treating RGB as independent would implement a different model.

The image adapter must pass normalization, conditional-probability, rank-inversion, and PNG save/load checks. Reuse cached network outputs within a pixel where the architecture permits, and benchmark full generation and replay before choosing the final trial count.

For a minimal image-conditioning experiment, supply one pre-shared 1 x 32 RGB row as a private causal prefix to a native 32 x 32 model. Generate the remaining 31 rows and transmit those rows as a **31 x 32 RGB PNG**. The receiver prepends the shared row internally before replaying the visible pixels. Use two fixed prefix rows drawn independently of the test payloads. Ordinary controls use exactly the same conditioning and crop.

This tests a small image fragment as conditioning context without a vision-language model. It also has an explicit cost: a pre-shared 96-byte row and a cropped native model canvas. The 31 visible rows provide a fixed budget of 2,976 channel values; an unfinished packet at that boundary is a capacity failure. Once the packet ends, sample all remaining pixels normally. A full image-key interface or a key overlay is unnecessary for this first result.

Do not substitute latent image codes unless their recovery from the delivered pixels is demonstrated. A decoder's access to the original latent IDs would recreate the saved-token problem in another modality.

**8. Meaning of a key and of asymmetry**

Keep three objects distinct: the published implementation/profile, the conditioning context that changes model probabilities, and the random encryption key that protects packet contents. Text prompts and image rows provide different kinds of conditioning. Their effective secrecy is not established by visual complexity or by large changes in the output.

The proposed study is asymmetric in its conditioning: prose for the text model and pixels for the image model. It remains a shared-secret protocol; it is not public-key cryptography. The shared row is an intentionally limited instance of your image-key idea. A complete image used through a multimodal encoder, semantic key matching, and composite mapping/overlay constructions each introduce another recovery problem and are deferred.

**9. A fixed experiment matrix**

Use 20 development payloads per direction, disjoint from 100 test payloads per direction. Choose 100 distinct source images for the canonical thumbnails. For text, use 50 messages of 32-64 UTF-8 bytes and 50 of 65-128 bytes from an appropriately licensed corpus. Put Unicode edge cases and synthetic image patterns in development checks. Do not truncate through a UTF-8 code point.

Use two fixed text prompts and two fixed image rows. These are controlled contexts, not a representative sample of all possible keys. Freeze source provenance, exclusions, preprocessing, contexts, seeds, packet construction, and thresholds before test generation.

| Allocation | Count |
| --- | ---: |
| Test payloads per direction | 100 |
| Contexts per payload | 2 |
| Coding methods | 3 |
| Directions | 2 |
| Total test stego artifacts | 1,200 |
| Ordinary controls, at most one per stego artifact | 1,200 |

Generate ordinary controls by sampling from the same eligible distribution and context. Match text controls to the realized carrier length; image controls have the same pixel dimensions. Deduplicate exact control artifacts for detection analyses and preserve shared-control dependencies in resampling. A small development comparison against unfiltered sampling can characterize the text consistency filter's own cost.

Pair methods by payload and context. Resample whole payload groups for confidence intervals, carrying their methods, contexts, and corresponding controls together. Do not treat multiple methods or two contexts as additional independent payloads. Use paired differences in rate, latency, and likelihood; use grouped intervals for recovery. Even 100/100 successful independent payload groups would not establish a 99.9% reliability claim.

**10. Measurements and hypotheses**

Pre-specify three questions:

1. Can the fixed and gated rank methods recover the source from the delivered artifact, with all framing information conveyed or fixed by the common profile?
2. How does gating change completion, net rate, and distributional distortion in each modality?
3. How do the rank methods compare with arithmetic coding when packet and carrier overhead are counted?

Report the following for each direction and method:

| Measurement | Definition or purpose |
| --- | --- |
| Artifact recovery | Exact payload recovery divided by every attempted trial |
| Completed-packet recovery | Exact recovery among completed encodings, reported alongside the previous row |
| Useful rate | Original payload bits divided by all delivered text tokens or all delivered image pixels |
| Transport rate | The 2,336 packet bits divided by carrier symbols through packet completion |
| Expansion | Delivered UTF-8/PNG file bytes divided by original payload bytes |
| Runtime | Encoding, decoding, and total seconds; model calls and peak memory |
| Distributional change | Conditional surprisal and rank statistics against matched ordinary samples |
| Overhead | Header, nonce/tag, slot padding, coder termination, skipped positions, and completion |

For images, distinguish bits per pixel from bits per channel value. For example, a 128-byte text in a 31 x 32 carrier has a useful rate of approximately 1.03 bits/pixel, irrespective of the four bits carried at each forced channel choice. For the fixed text method, 584 packet positions plus 32 completion tokens give 616 tokens if no support failure occurs; a 256-byte image then yields approximately 3.32 useful bits/token. These are protocol calculations, not experimental findings.

Measure surprisal separately at packet-bearing positions, over the span through packet completion, and over the entire artifact. Otherwise, ordinary image completion or text tails can dominate the average. The earlier RankCloak manuscript already demonstrates why that separation matters.

A useful diagnostic for uniform choice among the top 16 eligible symbols is its conditional divergence from the normalized ordinary distribution `q`:

`D = -4 - (1/16) * sum(log2(q(v_r)), r=1..16)`.

Use this to interpret the cost of a fixed four-bit rank decision. Entropy gating need not minimize this cost, and the relationship can differ between pixel and language models. This is a diagnostic under the uniform-rank model, not a new security theorem or an assumption that encryption makes finite packets perfectly independent fair bits.

**11. Keep detection bounded**

Compute exact-model/context-aware surprisal and rank-based scores, using the traces already needed for replay. Compare their ROC-AUC against matched ordinary controls and report grouped uncertainty. Label this as an observer who knows the generation model and conditioning context; the observer need not have the encryption key to score a carrier.

Use those results to characterize detectability and identify large artifacts from the protocol. Do not infer resistance to unknown detectors or human imperceptibility from low scores. Do not estimate very low false-positive operating points from this sample size. Neural detector training, human participant ratings, cross-model detection, and broad adversarial evaluation belong to a subsequent study.

On a fixed 20-case subset, re-save PNGs with another lossless compression setting and strip ancillary metadata; verify that unchanged pixel arrays still decode. Also verify raw UTF-8 save/load. Cropping visible content, JPEG recompression, and paraphrasing change the actual symbol sequence and remain outside the exact-channel contract. These checks reuse generated artifacts.

**12. Minimal implementation work**

Build a small extension with clear adapters, reusing focused primitives rather than copying the entire revision pipeline:

| Component | Reuse | New work |
| --- | --- | --- |
| Packet layer | Existing byte-handling conventions where applicable | Fixed header/slot, standard AEAD wrapper, strict parser |
| Rank coding | `rankcloak/rank_codec.py` | Pure packet-byte interfaces and strict length checks |
| Language backend | `model_io.py`, rank ordering, token filters | Complete-prefix consistency and UTF-8 artifact receiver |
| Entropy gate | `revision_v3_entropy.py` | Common model adapter and per-modality calibration |
| Image backend | Existing numerical rank primitives | Discrete pixel PMFs, prefix conditioning, PNG replay |
| Arithmetic comparator | Published implementation | Shared PMF adapter, finite termination verification |
| Evaluation | Existing manifests, timing, statistics, failure logs | Small paired matrix and artifact-only evaluator |

In particular, keep `decode_representation` separate from the new receiver: its current representation object contains source information useful for evaluation. The receiver should return recovered bytes or a structured failure; a different process compares those bytes with the source. [Current representation/replay implementation](https://github.com/mantzaris/llm-rankcloak/blob/ce853d42d6ba64065cb63c6bdfc0d825c62734cd/rankcloak/revision_protocol.py)

Meaningful tests cover all 256 byte values, packet authentication and bounds, UTF-8 boundary cases, forced support failure, arithmetic termination, PNG pixel equality, and independent receiver recovery. Preserve the first divergent symbol and the failure stage for diagnosis. Avoid building a large dashboard or training framework.

**13. Schedule, compute budget, and stopping rules**

Allow approximately six focused researcher-weeks, conditional on the image backend being usable. The following is an effort budget, not a promise about model throughput.

| Stage | Time box | Exit criterion |
| --- | --- | --- |
| Reuse audit and packet contract | 3 days | Fixed source/receiver interfaces and packet tests |
| Image feasibility and text serialization | 1 week | Fixed-rank recovery from both delivered artifact types on development examples |
| Gating and arithmetic comparator | 1 week | All methods invert finite packets; timing and calibration frozen |
| Development pilot and protocol freeze | 3 days | Full workload estimate fits the chosen budget |
| Main experiment and analysis | 1 week | Paired results, retained failures, uncertainty, representative examples |
| Manuscript and reproducibility package | 1-2 weeks | Claim-to-evidence table and repeatable release |

Set a default ceiling of **40 GPU-hours** for the development and main runs combined, using existing hardware as available. Measure full encode, decode, scoring, and control-generation costs in the pilot. Extrapolate by modality and method, with a 25% reserve. CPU time and researcher time should also be logged.

If the estimate exceeds the ceiling, reduce the second context to a development-only sensitivity check before freezing the test. This halves the main generation allocation while retaining both directions, all three methods, and 100 independent test payloads per direction. Do not drop a direction, discard difficult payloads, or omit the external comparator to preserve a larger sample matrix.

Stop after three working days of unresolved checkpoint/runtime problems rather than training a new image model. Document the blocker and rescope the schedule. Do not begin main runs until the fixed-rank artifact endpoint works. Budget exhaustion in a functioning gated or arithmetic method remains an experimental outcome, rather than a reason to conceal failed cases.

**14. The paper and its boundaries**

The paper should contain a short correctness argument under explicit assumptions: identical model state and ordering, reconstructible carrier symbols, sufficient eligible support, known packet framing, and successful finite termination. Show how those assumptions map to the two implemented serializers. Credit existing consistency and coding methods; present the argument as a protocol property.

Plan four principal figures: architecture and receiver inputs; artifact recovery and failure stages; useful rate versus distortion/runtime; and representative payload/carrier/recovered examples with payload-bearing locations identified for analysis. Two tables can summarize the frozen settings and main paired outcomes. Keep full traces and expanded diagnostics in the supplement.

The substantive comparison is whether simple rank transport retains a useful practical tradeoff once actual artifact recovery and all overhead are enforced. If arithmetic coding dominates it, report that result and explain the measured bottleneck. A generic bidirectional demonstration alone is insufficient grounds to claim a new steganographic principle.

Explicitly cite your earlier repositories/manuscript and identify inherited code and reused evaluation ideas. The new claim must rest on new cross-modal artifacts and experiments. Claims should remain limited to small canonical images, short text, the pinned models, and unchanged carrier symbols.

Defer high-resolution photographs, lossy semantic reconstruction, diffusion or latent-code carriers, image overlays, full multimodal image keys, key-collision enumeration, multilingual sweeps, quantization sweeps, custom error correction, new compression algorithms, and large detector/human studies. Each would change the experiment or recovery contract. The core study is complete when both directions work from delivered files and the three-method comparison explains their capacity, distortion, runtime, and failure costs.
