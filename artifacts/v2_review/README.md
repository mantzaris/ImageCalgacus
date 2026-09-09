# V2 bounded prospective review packet

The frozen allocation is complete: **120/120 stego outcomes, 40/40 independent controls, 100 exact recoveries and 20 retained arithmetic-text capacity failures**. Allocation completeness is not all-recovered success. No V1 GPU experiment was repeated.

| Direction | Fixed | Gated | Arithmetic A1 |
|---|---:|---:|---:|
| Image → saved UTF-8 → image | 20/20 | 20/20 | 0/20 |
| Text → saved PNG → text | 20/20 | 20/20 | 20/20 |

All cells have 20 held-out payload groups. The 95% Clopper–Pearson bounds are [83.16%, 100%] for 20/20 and [0%, 16.84%] for 0/20. These are small-sample working-model intervals, not broad reliability or power claims.

## Start here

- [Full results and interpretation](../../notes/v2_results.md), [CPU portability](../../notes/v1_test_portability.md).
- [Coverage](coverage.json), [acceptance](acceptance.json), [public verification](public_verification.json), [failures](failures.json).
- [Frozen manifest and analyses](manifest.json), [execution freeze](execution_freeze.json), [source/context provenance](../../data/qualification_v1/manifest.json).
- [Per-case results](results.jsonl), [recovery table](recovery_rates.csv), [paired differences](paired_differences.csv), [exploratory AUC table](detectability.csv), [machine-readable analysis](analysis.json).
- [Recovery plot](recovery.svg), [whole-carrier AUC plot](detectability.svg).
- [Controls](controls.json), [120 shared-control links](control_links.json), [receiver input-boundary checks](receiver_boundaries.json), [compact arithmetic audits](arithmetic_audits.json).
- [GPU jobs](gpu_jobs.json), [backend initialization](backend_initialization.json), [budget](budget.json), [compute projection](compute_projection.json), [preservation](preservation.json), [file hashes](artifact_hashes.json).

### Viewable examples

| Example | Source | Delivered carrier | Recovered |
|---|---|---|---|
| HI1 fixed | [PNG](cases/HI1-prompt1-fixed/source.png) | [UTF-8](cases/HI1-prompt1-fixed/carrier.txt) | [PNG](cases/HI1-prompt1-fixed/recovered.png), [raw pixels](cases/HI1-prompt1-fixed/recovered.gray) |
| HI1 gated | [PNG](cases/HI1-prompt1-gated/source.png) | [UTF-8](cases/HI1-prompt1-gated/carrier.txt) | [PNG](cases/HI1-prompt1-gated/recovered.png) |
| HI1 A1 failure | [PNG](cases/HI1-prompt1-arithmetic/source.png) | [retained UTF-8](cases/HI1-prompt1-arithmetic/carrier.txt) | No authenticated payload |
| HT1 fixed | [UTF-8](cases/HT1-row1-fixed/source.txt) | [PNG](cases/HT1-row1-fixed/carrier.png) | [UTF-8](cases/HT1-row1-fixed/recovered.txt) |
| HT1 gated | [UTF-8](cases/HT1-row1-gated/source.txt) | [PNG](cases/HT1-row1-gated/carrier.png) | [UTF-8](cases/HT1-row1-gated/recovered.txt) |
| HT1 A1 | [UTF-8](cases/HT1-row1-arithmetic/source.txt) | [PNG](cases/HT1-row1-arithmetic/carrier.png) | [UTF-8](cases/HT1-row1-arithmetic/recovered.txt) |

All 120 carriers, not just these first-manifest examples, are retained under cases/. PNGs are 32×31 RGB8 after withholding the shared conditioning row. Recovered images are canonical 16×16 grayscale.

## CPU-only public verification

From the repository root, with the declared CPU dependencies:

~~~sh
python -B -m unittest discover -s tests -v
python -B scripts/collect_v2_review.py --verify-public artifacts/v2_review
python -B scripts/analyze_v2.py --review artifacts/v2_review
python -B scripts/finalize_v1_qualification.py --verify-public artifacts/v1_qualification_review
~~~

The public verifier checks complete allocation, saved-source equality, hashes, declared model/profile/context identities, packet-pairing digests and matched-control links. Exit 0 means complete valid evidence, **not** recovery of every payload. It neither reads keys nor performs neural decoding. Analysis reproduction preserves statistical hash 05da416e55a220fe1659328ba44ffcc0dce20ad937d35f7294e25c37d64a1d61 and all CSV/SVG outputs; CPU timing metadata can differ.

Final clean-export tests: 71 passes and two explicit skips (private historical integration; pinned source cache). Locally, with retained prerequisites and IMAGECALGACUS_PRIVATE_TESTS=1, all 73 passed. The real model-free Linux child check passed. [Final CPU evidence](final_cpu_verification.json) distinguishes those scopes and the zero-cost completed-run continuation check.

## Boundaries and interpretation

All 280 model processes verified actual GPU execution: text full 33/33 eligible-layer offload; image strict CUDA loading/input placement. New charged time is **42,024.527642s**; cumulative V0+V1+V2 is **85,183.689935s**. V2 has 11,975.472358s unused; whole-project actual headroom is 58,816.310065s. The one-reserve forecast is 29.57767 hours, not additional spend or execution permission.

All arithmetic text failures reached the unchanged token cap with matching partial prefixes and insufficient accumulated information. Raw A1 classifier flags in HI5/HI16 reflect isolated non-narrowing steps; no sustained stagnation was observed. HT19 arithmetic PNG also had one isolated step and recovered exactly. The separately documented A1 algorithmic stagnation limitation remains. No full arithmetic text recovery is established.

Scores are exploratory, whole-carrier, known-model/context mean surprisal and log2-rank. Their higher-is-stego directions and grouped intervals were frozen before outcomes. Failed carriers remain scorable observations; controls/prefixes are shared, not extra independent method replicates. No duplicate-control or unscorable V2 cases occurred. Small-sample separation is not imperceptibility or unknown-detector resistance.

Keys, sealed packets, weights, environments and raw private bit/interval traces are excluded. Private paths in command records are provenance references only. These public case directories contain ground truth: **never use them directly as receiver inboxes**. Actual receivers received only carrier/profile/context/key in separately staged directories.

Accepted evidence remains in [V1 qualification](../v1_qualification_review/README.md), [V1.2](../v1_2_review/README.md), [V1.1](../v1_1_review/README.md), [V1 pilot](../v1_review/README.md) and [V0](../v0_review/README.md). All 4,827 protected historical files are unchanged. The unavailable historical static-arm control prefix stays unavailable. No additional lossless replays, sweeps, scoring passes, manuscript, commit, push or publication were performed.
