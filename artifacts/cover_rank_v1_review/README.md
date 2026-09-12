# cover_rank_v1 review packet

The bounded photograph-preserving study is complete. All 12 development and 40 held-out carriers recover exactly from saved PNGs. This is a separate extension, not a rerun or replacement of the accepted generated-image study.

The model produces reproducible partitions distinct from simple parity. It does **not** demonstrate an advantage over parity in recovery, fidelity or runtime. The twenty held-out model-rank carriers average 70.255 dB PSNR and 0.9999664 SSIM. Parity averages 70.398 dB and 0.9999688. Both recover 20/20. These are descriptive paired results, not steganalysis or human-observer evidence.

## Inspect the results

- [Protocol and correctness argument](../../plan/cover_rank_v1.md), [implementation/results notes](../../notes/cover_rank_v1_results.md).
- [Frozen allocation and data provenance](manifest.json), [profile](profile.json), [initial execution identity](execution_freeze.json), [post-development freeze and forecast](heldout_freeze.json).
- [Per-case JSONL](results.jsonl), [per-case CSV](per_case.csv), [paired differences](paired.csv), [paired summary](paired_summary.json).
- [Summary CSV](summary.csv), [Markdown table](summary.md), [LaTeX table](summary.tex), [captions](captions.md).
- [Complete text/photo example PDF](text_photo_example.pdf), [SVG](text_photo_example.svg), [PNG](text_photo_example.png).
- [Three fixed-identifier examples and differences PDF](cover_examples.pdf), [SVG](cover_examples.svg), [PNG](cover_examples.png).
- [Acceptance and checks](acceptance.json), [final verification record](verification.json), [six development receivers](development_checks.json), [compact jobs and GPU reports](jobs/).
- [Accounting](budget.json), [output provenance](output_provenance.json), [private preservation audit result](private_preservation_check.json).
- [Integrated manuscript](../../paper/icaart2027/README.md), with the photograph example in main Figure 2 and paired results in Table 3.

Every group has its canonical cover and literal source under `cases/`. Every arm has its delivered carrier, recovered text and terminal record under `outcomes/`. For example, [source](cases/heldout-2018/source.txt), [cover](cases/heldout-2018/cover.png), [delivered model-rank PNG](outcomes/heldout-2018-model_rank/carrier.png), and [recovered text](outcomes/heldout-2018-model_rank/recovered.txt). The two arms share one immutable sealed packet and exactly the same selected positions. Packet contents, keys and private receiver inboxes are not in this collection.

## Protocol and receiver boundary

For a 256 × 256 RGB8 cover, B = c & 252 is invariant and B + 2 is the reconstructible model context. The GPU evaluates 64 independent 32 × 32 tiles, one map forward each. At every selected pixel, all 64 cell colors receive correct joint RGB log probabilities with candidate-specific within-pixel conditioning. Descending log probability, then lexicographic RGB, determines rank parity. The sender selects the nearest candidate in the required bit class, with lexicographic distance ties. The baseline substitutes channel-sum parity and changes nothing else.

A domain-separated HKDF/HMAC placement rule uses the retained run key, coarse image and agreed profile, not the hidden nonce. The receiver receives only PNG, profile/arm and key. It reconstructs the context and ranks independently. It does not receive the original cover, source, packet, rank maps, traces or evaluator files. Each receiver runs after sender exit in a fresh process with a three-file input directory. Public review files are evaluator evidence, not receiver inputs.

The 292-byte authenticated packet and payload restrictions are unchanged. Packet success, saved carrier completion, authentication and independent source equality are recorded separately. These scores define the new coarse-context embedding rank map, not the accepted V2 likelihood of the final image under its full-precision history.

## Verification and failures

All 52 source comparisons, 52 coarse-invariance checks and channel bounds pass. Every model sender/receiver pair has identical parameter-map, log-score and ordering digests. The three-tile development probe produces exact reference/graph maps and agrees with the existing conditional probability oracle to at most 1.0658141036401503e-14 log units. This independent-formula error is not a tolerance for differing sender/receiver streams.

Four deliberately invalid verification inputs, wrong key and changed first transported packet bit for each arm, are rejected with InvalidTag and no plaintext. The flipped bit is in the packet nonce. Two compression-9 PNG re-saves preserve pixel bytes and recover exactly. These six checks are not independent new carriers. There are no unexpected protocol, capacity or infrastructure failures, replacements or success-seeking retries.

Seven new focused CPU tests and six existing relevant GPU/profile/accounting tests pass. Public verification recomputes metrics and checks exported values, identities, hashes, completeness and recorded statuses. It cannot independently authenticate without the retained private key. The private audit additionally checks the actual ledger and 11,851 protected historical files and scans this directory for key/packet representations.

## Reproduction

Use the existing Python dependencies, not a new environment. From the repository root:

```sh
python -B scripts/analyze_cover_rank_v1.py --verify-only
python -B scripts/analyze_cover_rank_v1.py
```

The second command rebuilds only CPU tables and figures from public saved evidence. Neither command loads weights, uses keys, downloads data or runs inference. The execution host used `../llm-rankcloak/.venv/bin/python`; that is an explicit interpreter choice, not an implicit sibling import. The existing NumPy, SciPy, Pillow and Matplotlib stack suffices for analysis.

The following commands actually ran in the authorized private GPU environment:

```sh
python -B scripts/prepare_cover_rank_v1.py
python -B -m imagecalgacus.cover_rank_study --through probe
python -B -m imagecalgacus.cover_rank_study --through development
python -B -m imagecalgacus.cover_rank_study --through all
python -B scripts/analyze_cover_rank_v1.py --verify-only --private-audit
```

Preparation refuses to overwrite an existing manifest or re-encrypt its groups. The retained continuation command skips complete outcomes; a completed-run invocation was verified to launch zero additional jobs. Fresh GPU reproduction needs compatible CUDA, the exact checkpoint and retained private packets/keys. It is not part of public verification and no further execution is requested here. Individual encode/decode command arrays are retained in `jobs/`; model paths in those records are provenance, not bundled dependencies.

## Accounting and hardware

The extension's absolute cap is 7,200 seconds, applied idempotently. Total charge is **429.149258 seconds**, leaving **6,770.850742 seconds**. Of 111 charged child processes, 56 neural jobs account for 387.756360 seconds and 55 model-free children account for a conservatively charged 41.392898 seconds. Loading, warmup, occupied CPU work, serialization, expected failures and teardown are included once. Cumulative history is **89,404.217194 seconds**, leaving **54,595.782806 seconds** below the 144,000-second ceiling. Unused allowance is not spent compute.

The model runs on NVIDIA RTX 5000 Ada Generation, physical device 1 mapped to logical CUDA 0, with the exact device UUID in the profile. PyTorch 2.5.1+cu124, float32 network inference, float64 candidate bookkeeping, strict checkpoint loading, evaluation/inference mode, deterministic settings and the accepted CUDA graph path are unchanged. All 56 neural jobs have positive process-specific pmon samples and CUDA input/parameter placement. Sampling is intermittent and does not establish sustained utilization. Model-free parity has no neural inference and is not a CPU model benchmark.

## Provenance, attribution and limitations

Starting source revision is `e39c14cc858bb67f870916692384d0e97502aa63`. The frozen file identities distinguish new implementation from historical execution. Existing ImageBackend/CUDA graphs, PixelCNN++ model, conditional functions, AES-GCM packet/parser and budget machinery are reused. RankCloak at `ce853d42d6ba64065cb63c6bdfc0d825c62734cd` supplies the established CUDA/replay environment conventions; its pipeline is not imported. Existing attribution and license notices remain.

BSDS500 comes from the BIDS mirror at `a04b7c6c3a9f0ace74bf205c72a43d32e1c72722`, January 2013 distribution. The smallest numeric train identifiers select six development covers, and the smallest test identifiers select twenty held-out covers. RGB conversion and floor-offset center crops do not resize images. Source JPEG hashes, URLs, partitions, crop boxes, canonical hashes and retained text assignments are in the manifest. There are twenty independent evaluation cover/text groups, not forty independent arm observations. No held-out outcome influenced selection.

Cite Arbeláez, Maire, Fowlkes and Malik, “Contour Detection and Hierarchical Image Segmentation,” TPAMI 33(5), 898–916, 2011, DOI 10.1109/TPAMI.2010.161. See the retained [mirror notice](BSDS_MIRROR_README.md). A blanket photograph republication license was not identified. These local research/review derivatives are not relicensed under project MIT; the author must confirm publication reuse. Retained Gutenberg source terms also apply.

The learned partitions differ from parity up to label swap at all 46,720 selected held-out positions, with mean normalized disagreement 0.44843549. Distinction is not benefit. No comparison with syndrome-trellis coding, trained watermarking or steganalyzers was executed. Fidelity does not establish undetectability. Authentication does not cover unused low bits or every photograph pixel. The old V2 detection AUCs do not apply to this carrier. All accepted evidence remains unchanged.
