# Photograph-preserving model-rank extension

## Outcome and scope

Completed from clean revision `e39c14cc858bb67f870916692384d0e97502aa63`. All six development covers and twenty held-out covers passed in both arms, totaling 52 exact authenticated recoveries from saved PNGs. No original carrier was replaced or retried for success. This is a new, separate `cover_rank_v1` experiment, not a revision of V0/V1/V2 or the GPU benchmark.

The [review index](../artifacts/cover_rank_v1_review/README.md) links all cases, measurements, compact jobs and publication outputs. The scientific contribution is reproducible model-rank embedding within a reconstructible invariant cover context, with an explicit distortion bound and independent artifact recovery. **The learned partitions did not add a demonstrated benefit beyond simple parity in this comparison.**

| Held-out descriptive mean | Model rank | Simple parity |
|---|---:|---:|
| Exact authenticated recovery | 20/20 | 20/20 |
| PSNR, dB | 70.254794 | 70.398374 |
| SSIM | 0.9999664123 | 0.9999687999 |
| Maximum channel change over cases | 2 | 1 |
| Changed pixels, % | 1.781235 | 1.780014 |
| Changed channels, % | 0.613276 | 0.593338 |
| PNG bytes | 116772.85 | 116762.50 |
| Useful source bytes | 93.2 | 93.2 |
| Fresh-process sender, s | 6.997581 | 0.823067 |
| Fresh-process receiver, s | 6.884328 | 0.685508 |
| Sender plus receiver, s | 13.881909 | 1.508575 |

Per-case values, ranges and paired differences are calculated from saved artifacts and unrounded job records. There are twenty evaluation groups, not forty independent arm observations. Model-minus-parity paired mean PSNR is −0.143581 dB, SSIM −0.00000238767, PNG size +10.35 bytes and process time +12.373334 seconds. No new inferential test, detector or human rating was added.

## Implemented components and reuse

- `imagecalgacus/cover_rank.py` implements reconstructible keyed placement, joint RGB log ranks, nearest-candidate embedding, saved-PNG recovery and the development probe. The parity arm shares all machinery except labeling and neural calls.
- `imagecalgacus/cover_rank_study.py` is a small serial continuation entry point using the existing budget wrapper, atomic records and explicit input directories.
- `scripts/prepare_cover_rank_v1.py` freezes deterministic data/packet bindings. It refuses to overwrite the manifest or re-encrypt an existing run.
- `scripts/analyze_cover_rank_v1.py` recomputes metrics and publication outputs from public evidence. Verification checks exported CSV/JSON values against fresh CPU calculations, without model execution.
- `imagecalgacus/runtime.py` adds only a stage-specific idempotent 7,200-second authorization. Other phase limits, old ledgers and the 144,000-second cumulative cap are unchanged.

The existing ImageBackend CUDA graph forward interface, strict checkpoint loader, PixelCNN++ architecture, pixel conditional implementation, 292-byte AES-GCM packet/parser, PNG reader and accounting conventions are reused. Accepted image/text inference and probability code are unchanged. No old pipeline was copied. Local RankCloak revision `ce853d42d6ba64065cb63c6bdfc0d825c62734cd`, its NVIDIA setup and model I/O/replay precautions were inspected. The established interpreter and CUDA environment were reused without installations or modifications to RankCloak. Existing attribution and third-party restrictions remain.

## Frozen protocol

For every channel, B = 4 floor(c/4). Every delivered pixel lies in the same 4 × 4 × 4 RGB cube. The canonical model input is B + 2. The image is divided into 64 row-major 32 × 32 tiles. One GPU map forward per tile supplies all pixel parameters; there is no candidate-wise or bit-wise autoregressive generation loop.

All 64 candidate colors are scored in the log domain. The discretized logistic mixture retains the actual candidate red value in green conditioning and candidate red/green in blue conditioning. Log-sum-exp combines mixture terms. Descending joint log probability with lexicographic RGB ties defines zero-based rank parity. No candidate is removed due to normalization underflow. The sender minimizes squared RGB distance within the required class and breaks distance ties lexicographically.

Placement derives a domain-separated key with HKDF-SHA256 from the run key and coarse-image hash, then orders all raster positions by HMAC-SHA256 priorities bound to the agreed protocol. The first 2,336 distinct positions carry packet bits, MSB first. The hidden nonce is not an input to placement. The profile excludes arm from the shared placement identity. One fresh run key and 26 unique random nonces seal 26 immutable packets, reused across paired arms. Cryptographic randomness is not derived from a sampling seed.

The receiver takes only saved PNG, declared profile/arm and retained key. It reconstructs B, B + 2, positions and ranks independently. Original cover, source bytes, prepared packet, encoder state and rank maps are excluded. Receiver imports/data flow do not load evaluator records. Three-file receiver directories contain only carrier, profile and key. Sender exits before receiver launches. Equality is checked by the runner/evaluator afterward. Authentication is not a guarantee against changes to unused image bits.

Scores are a new coarse-context embedding rank map, not the original V2 likelihood under actual full-precision pixel history. The simple parity baseline labels the same candidates by (r + g + b) mod 2. It is not a state-of-the-art steganography comparison.

## Sources, selection and freezing

The BIDS BSDS500 mirror is pinned at `a04b7c6c3a9f0ace74bf205c72a43d32e1c72722`. Only the selected 26 JPEGs were downloaded. The six smallest numeric train identifiers and twenty smallest numeric test identifiers were frozen before embedding. RGB conversion and centered floor-offset 256 × 256 crops use no resize. The manifest records partition, URL, source hash, original dimensions, crop rectangle and canonical file/pixel hashes. Canonical crops are unique and train/test identifiers are disjoint.

Development text assignments use T1–T6, including a valid non-ASCII fixture. Evaluation uses the retained HT1–HT20 literal byte sequences, 58–128 bytes. Text selection, offsets, hashes and source terms are copied from the frozen source manifest, not chosen from image outcomes.

The initial execution file-hash freeze precedes the probe and twelve development carriers. After all development checks passed, the held-out freeze recorded the same code/profile identities and a 1,400-second conservative complete-batch forecast against 7,078.660 remaining seconds. No protocol changes were made after this freeze. The first three test identifiers define the difference figure, and the first defines the complete transport example.

BSDS attribution is Arbeláez, Maire, Fowlkes and Malik, TPAMI 33(5), 898–916 (2011), DOI 10.1109/TPAMI.2010.161. The mirror's research distribution did not establish blanket photograph republication rights. Local research/review derivatives are retained without claiming MIT ownership. The author must confirm figure publication permissions. Original JPEG cache, run keys and sealed packets remain ignored private files.

## Correctness and focused validation

1. All 52 delivered PNGs preserve B exactly and meet |channel change| ≤ 3.
2. The independent conservative bound is SSE ≤ 2,336 × 3 × 9 = 63,072. Dividing by 256 × 256 × 3 and using peak 255 gives **53.0684494361 dB**. Measured PSNR is reported separately.
3. The first development cover's three predetermined tiles produce identical reference/CUDA graph parameter maps. The correct joint log formula agrees with the existing channel-conditional oracle to at most **1.0658141036401503e−14** log units.
4. All 26 model sender/receiver pairs reproduce exact map, candidate-score and ordering digests across fresh GPU processes. No tolerance is used for this equality.
5. All 52 original packets authenticate and all 52 source-byte comparisons pass. Literal UTF-8 output is retained.
6. For each arm, one wrong-key check and one changed first embedded packet bit produce InvalidTag without plaintext. The flipped transported bit is in the packet nonce. These are four expected negative checks, not carrier failures.
7. One compression-9 PNG re-save per arm preserves dimensions/mode/pixel bytes and recovers exactly in a fresh receiver.
8. Seven focused extension CPU tests pass, plus six existing relevant GPU/profile/accounting tests. A constant-image SSIM fixture agrees with its independent closed form within 1.12e−16; its PSNR agrees with 20 log10(255).
9. The final completed continuation command launches zero jobs. Public metrics/status/identity checks pass. The private audit confirms 11,851 protected files unchanged and scans public outputs for raw, hexadecimal and Base64 key/packet material.

No unexpected execution, numerical, authentication, capacity or infrastructure failure occurred. No model training, CPU model inference, new text-carrier run or additional experimental matrix was performed.

Every selected held-out learned partition differs from parity even allowing a global bit-label swap, 46,720/46,720. Mean minimum Hamming fraction is **0.4484354934**, with per-image means 0.446583–0.451158. This establishes a different learned partition, not superiority. Model fidelity and runtime are worse than the simple baseline in the reported means.

## GPU evidence and accounting

The existing NVIDIA RTX 5000 Ada Generation (32 GB), physical GPU 1 mapped to cuda:0, is recorded by UUID in the profile. Runtime is Python 3.10.13, PyTorch 2.5.1+cu124 and driver 590.48.01. The pinned checkpoint hash starts `a5ed558f6d4098ce` and its full identity is in the manifest/profile. Model float32, candidate math float64, CUDA graph execution, deterministic settings, eval/inference mode and strict loading are unchanged.

All 56 neural processes have positive PID-specific pmon activity and CUDA parameter/input evidence. Sampling is intermittent, not a sustained-utilization estimate. Mean held-out model phase encode/decode times are 2.122004/1.982842 seconds, with mean model loading 0.973071/0.981608 seconds. These are nested inside the fresh-process totals, not additional charges.

| Accounting boundary | Seconds |
|---|---:|
| Prior V0/V1/V2/benchmark/context history | 88975.067936 |
| New neural occupied processes, 56 jobs | 387.756360 |
| Model-free children conservatively charged, 55 jobs | 41.392898 |
| Extension total, 111 jobs | **429.149258** |
| Remaining extension cap | **6770.850742** |
| Whole-project cumulative | **89404.217194** |
| Remaining to 144000-second ceiling | **54595.782806** |

The 111 jobs comprise 104 original sender/receiver jobs, six verification receivers and one three-tile probe. All loading, warmup, CPU processing while occupied, serialization, failures and teardown are counted. No unused allocation is counted as spending. No comparison with V2's different generation workload is used to claim speedup.

## Outputs and manuscript integration

The review packet provides two figures as PDF, SVG and 400-dpi PNG, plus per-case/summary/paired CSVs and a Markdown/LaTeX table. Absolute differences are amplified exactly 32×; original and carrier files are unmodified by plotting. Main Figure 2 shows the actual first photograph transmission, and Table 3 reports both arms. Main Figure 1 still shows actual historical image-to-text and generated-PNG examples. The existing GPU performance plot moves to the companion, with its main numerical result retained.

The main draft remains 12 pages and the companion has 11. The current 184-word abstract and measured character counts are in the manuscript verification record. The official template is unchanged. The paper discusses Calgacus rank transfer, QIM, additive-distortion steganography, HiDDeN and StegaStamp with verified primary references. It claims the demonstrated invariant-context construction, not invention of invisible hiding or superiority to established methods.

No trained detector, human study, arbitrary image-file recovery or lossy robustness is established for this profile. Existing V2 detection AUCs are not reassigned to it. The model has not demonstrated additional fidelity, recovery or speed benefit over parity. Separate supplementary-upload permission and AI-disclosure placement remain venue-policy questions; photograph publication rights require author review.

## Commands and final boundary

See the review README for public analysis and private GPU reproduction commands. Focused CPU command:

```sh
../llm-rankcloak/.venv/bin/python -B -m unittest discover -s tests -p test_cover_rank.py -v
../llm-rankcloak/.venv/bin/python -B -m unittest discover -s tests -p test_gpu_performance.py -v
../llm-rankcloak/.venv/bin/python -B scripts/analyze_cover_rank_v1.py --verify-only --private-audit
python -B paper/icaart2027/build.py
python -B paper/icaart2027/package_source.py
```

These reporting/build steps add zero GPU time. Historical scientific artifacts and ledgers remain unchanged. No commit, push, publication or submission was performed. The extension stops at this completed 26-group comparison.
