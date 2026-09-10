# PNG detectability under one mismatched conditioning row

Completed: **80/80 PNGs fully scored**, with no scoring failures or exclusions. The primary fixed-rank AUC fell under row2, while fixed and gated mean-surprisal scores remained informative in this small sample. The extension used **1439.645 charged seconds**; accepted historical evidence is unchanged. [Review index](../artifacts/png_context_detection_review/README.md).

## Scope and starting evidence

This authorized extension asks whether an observer's whole-PNG detection scores change when it knows the exact image model and scoring procedure but supplies frozen development row2 instead of the sender's row1. It scores existing carriers only. Accepted V2 transmissions, controls, failures, analyses and the later engineering benchmark remain separate historical evidence.

Starting checkout: `cdff18c30a0492f242921d72fb369ef78a6a7f38`. Its only commit after reviewed GPU benchmark `5e08a8b` added the publication package, generation script and reporting note. No established coding, probability, model, serialization or sampling implementation is changed here.

The allocation is the 60 accepted V2 text-to-image stego PNGs and their 20 independent ordinary PNG controls. Each control belongs to one of 20 frozen payload groups and is shared across that group's three methods. Existing row1 scores are reused; no V2 row1 scoring or new carrier generation occurs.

## Observer and context contract

`imagecalgacus.png_observer` accepts exactly carrier, profile, context and output-report paths. Its input directory contains only a saved PNG, the common existing fixed profile and a row file. The profile's coder settings are not used. Class labels, payload-group/control links and retained reference scores are read only by the coordinating and analysis processes, never by the observer. No cryptographic key, plaintext, packet, sender representation or decoding state is required or supplied.

The observer prepends the supplied 96-byte RGB row to the unchanged 32-wide × 31-high delivered RGB8 pixels. It scores all 2,976 delivered channel values in raster R/G/B order, excluding the shared row from the score. The unchanged CUDA graph PixelCNN++ backend performs 992 model forwards, maintaining the exact discretized mixture RGB conditionals and mixture posterior updates. Network inference is float32, conditional bookkeeping float64. The existing `Trace.whole` sequential accumulator supplies mean eligible-distribution surprisal and mean log2 rank. The code does not infer packet boundaries, sample symbols or invoke a coder.

Observed symbols outside numerical support, nonpositive/nonfinite selected probability or incomplete scoring are explicit failures. There is no new probability floor, clipping, score imputation or use of partial means as a full-carrier score.

Row identities and construction are retained in the [extension manifest](../artifacts/png_context_detection_review/manifest.json):

- Row1: SHA-256 `0195319d7c029c97f4e79336b0494a74c39849f1836ad39c84f43a58278bcbc3`; the unchanged first row of the original ordinary seed-2001 feasibility canvas.
- Row2: SHA-256 `c7f5500001d4376a74183225a88ececc5541e2bde1d79a30961ff458073ae5e1`; the already frozen V1.2 row constructed with NumPy PCG64(2002), 96 uniform RGB8 values, independent of payloads and model outputs. No row was selected or modified using detection performance.

The new review packet contains row identities/provenance, not a new disclosure of raw conditioning bytes. Existing local context paths and the project's established disclosure/access policy remain unchanged.

## Focused validation and execution freeze

Six focused non-model tests passed: literal context selection and complete saved-pixel accounting, unsupported-symbol failure without clipping, allocation/shared-control identity, idempotent separate allowance with historical caps preserved, whole-project cap enforcement and coupled bootstrap orientation. A separate CPU check exactly reproduced all six accepted PNG AUCs and intervals using the existing analysis helpers. These are supporting engineering checks, not scientific observations.

Three predetermined development GPU jobs passed under their original row1: T1 fixed and T1 arithmetic reference carriers from the accepted GPU benchmark, and control-image-5202 (the first row1 ordinary control retained in the qualification review). All retained whole-score fields matched exactly, with no tolerance. Both available exact eligible-ID, probability and rank-order stream digests also matched at all 2,976 steps; the ordinary control had no historical stream digest to compare. Validation cost was 51.870883030991536 charged seconds.

The [execution freeze](../artifacts/png_context_detection_review/execution_freeze.json) pins code, existing profile, accepted source manifests, all 80 PNG identities, contexts, development checks, execution order and statistical rules before new V2 scoring. The private preservation inventory covers 11,269 pre-existing artifact/run/log/configuration/data/note/plan files, including retained keys and packets. Its contents are not exported.

The unchanged runtime is reused with one small addition: a separately named, absolute, idempotent 7,200-second PNG-context allowance. Previous stage caps and ledgers remain intact; cumulative usage is also capped at 144,000 seconds. The serial runner uses the existing global GPU lock, interrupted-process reconciliation, process-specific monitoring and 60-second hard job bounds. Atomic reports/terminal records prevent duplicate completed work on continuation.

The image runtime remains the existing RankCloak environment: PyTorch 2.5.1+cu124, selected RTX 5000 Ada UUID `GPU-10d1f16f-9e79-08bb-b2ba-3353c04422cf`, with strict checkpoint loading, CUDA model/input placement, evaluation/inference modes, unchanged deterministic numerical settings and exact graph path. RankCloak README GPU precautions and revision-v3 requirements were inspected at `ce853d42d6ba64065cb63c6bdfc0d825c62734cd`; no new external implementation was copied. Existing attribution remains in THIRD_PARTY.md.

Measured development jobs took 17.225–17.365 charged seconds each. The pre-batch forecast used a conservative 30 seconds per artifact (at least 1.5× the largest measured job), or 2,400 seconds for all 80, against 7,148.129 seconds remaining in this extension. This is one forward margin, not another charge. The entire frozen batch was authorized by that gate.

## Analysis fixed before row2 scoring

Primary score: whole-carrier mean eligible-distribution surprisal. Secondary: whole-carrier mean log2 rank, obtained in the same inference pass. Higher values always indicate stego, even when AUC is below 0.5. No classification threshold is selected.

The existing AUC, PCG64 grouped-draw and percentile-interval helpers are reused with 2,000 replicates and seed 2026090902 (accepted V2 base seed plus its PNG direction offset). Every draw resamples the same 20 payload groups within their frozen UTF-8 length strata, jointly carrying both observer conditions, all three stego methods and each shared control. Differences are computed inside each draw as row2 AUC minus row1 AUC, not by subtracting interval endpoints. There are 20 independent groups and controls, not 60 independent pairs.

The frozen allocation has 80 distinct PNG hashes, so the accepted duplicate-control ownership rule removes none. Scoring failures remain explicit; a method/score's paired analysis excludes only groups without both required condition scores and identifies them, while retaining the accepted full row1 result separately. No partial scores are substituted.

## Results and handoff

| Method | Correct row1 AUC | Mismatched row2 AUC [95% CI] | Paired change [95% CI] |
|---|---:|---|---|
| Fixed rank | 0.8850 | 0.6975 [0.5150, 0.8700] | -0.1875 [-0.2775, -0.1000] |
| Entropy gated | 0.8300 | 0.7475 [0.6074, 0.8825] | -0.0825 [-0.1625, 0.0100] |
| Arithmetic A1 | 0.5575 | 0.5925 [0.4124, 0.7725] | +0.0350 [-0.0225, 0.1050] |

All method/score cells contain 20 scorable stego PNGs and 20 unique matched controls, with 2,000 valid bootstrap replicates. Every PNG has 2,976 scored channels and 992 scoring forwards; existing graph warmup/capture forwards are additional setup work included in each job's charge. All 83 jobs (three development validations and 80 row2 scores) have positive process-specific GPU activity. No errors, timeouts, retries, clipping changes, exclusions or duplicate credits occurred. These new scores are repeated measurements of existing artifacts, not new independent transmissions.

The fixed-rank primary reduction is supported by a paired interval wholly below zero. Gating's lower point estimate is not a resolved reduction: its change interval includes zero. A1's small increase is likewise uncertain, and its row2 AUC interval includes 0.5. Fixed and gated primary row2 intervals are above 0.5, so this particular mismatch does not remove all information from the tested mean-surprisal observer.

The secondary mean-log2-rank results are retained in the [full comparison table](../artifacts/png_context_detection_review/comparison.md). Fixed rank decreases from 0.8400 to 0.6625 (paired change −0.1775, CI [−0.2800, −0.0950]), but its row2 marginal interval [0.4725, 0.8475] includes chance. Gated and A1 secondary changes also include zero. The statement about informative fixed-rank scores under mismatch therefore concerns the primary mean-surprisal score, not every score.

### Manuscript-ready Results paragraph

On the same 60 held-out stego PNGs and 20 shared ordinary controls, replacing correct conditioning row1 with previously frozen row2 reduced mean-surprisal AUC for fixed-rank coding from 0.8850 to 0.6975 (paired change −0.1875, 95% CI [−0.2775, −0.1000]). For gated coding, AUC changed from 0.8300 to 0.7475 (−0.0825 [−0.1625, 0.0100]); for arithmetic A1, it changed from 0.5575 to 0.5925 (+0.0350 [−0.0225, 0.1050]). All 80 artifacts were fully scorable. Intervals used 2,000 length-stratified resamples of 20 payload groups, preserving both observer conditions, methods and shared controls. Under row2, the primary fixed and gated AUC intervals remained above 0.5, whereas the A1 interval included chance and the gated/A1 change intervals included zero. Thus this mismatch weakened the tested fixed-rank score without eliminating informative mean-surprisal scores; the changes for gating and A1 remained uncertain. These results concern one alternate row with the exact model known, not fully blind detection or cryptographic secrecy.

### Accounting and evidence preservation

| Charged component | Seconds |
|---|---:|
| Historical v0 (unchanged) | 3163.653124 |
| Historical v1 (unchanged) | 39995.509169 |
| Historical v2 (unchanged) | 42024.527642 |
| Historical gpu_performance (unchanged) | 2351.732528 |
| Development score reproduction | 51.870883 |
| New row2 scoring of 80 PNGs | 1387.774590 |
| New extension total | 1439.645473 |
| Cumulative project usage | 88975.067936 |

The component and total rows overlap; they are not separate charges. New usage is 0.3999 GPU-hours. The extension retains 5760.355 seconds of its 7,200-second allowance. Whole-project usage is 24.7153 hours, leaving 55024.932 seconds (15.2847 hours) below the 40-hour ceiling. Unused authorization is not spent compute or permission for another extension. No model work remains in this allocation.

The 83 jobs ranged from 17.182 to 17.683 charged seconds. Process-specific `nvidia-smi pmon` samples had per-job median intervals of approximately 0.174–0.197 seconds and positive sampled activity in every job; these samples do not establish sustained utilization. Model CUDA-event durations are nested within scoring phases and are not added to occupied-process charges. Per-job loading, scoring, setup, memory, exact distribution digests and device evidence remain in the compact reports and job records.

Final preservation verified all **11,269 pre-existing files byte-for-byte**, including accepted V0/V1/V2, GPU benchmark and publication packages, private packets/keys and historical ledgers. The public verifier independently reconciles the 80 saved PNG identities, 20 control identities, complete scoring, reports and paired analysis without keys or inference. No plaintext, encryption key, packet bytes, new raw conditioning bytes, model files or private per-step audit traces are exported.

### Outputs, verification and limitations

- [Figure PDF](../artifacts/png_context_detection_review/context_auc.pdf), [SVG](../artifacts/png_context_detection_review/context_auc.svg), [400-dpi PNG](../artifacts/png_context_detection_review/context_auc.png): one figure, two panels (paired conditions and paired changes), 7.2 × 3.25 inches.
- [Comparison CSV](../artifacts/png_context_detection_review/comparison.csv), [LaTeX](../artifacts/png_context_detection_review/comparison.tex), [Markdown](../artifacts/png_context_detection_review/comparison.md): one six-row table, both frozen scores. Display rounding does not alter the unrounded evidence.
- [Captions](../artifacts/png_context_detection_review/captions.md), [per-artifact results](../artifacts/png_context_detection_review/results.jsonl), [analysis](../artifacts/png_context_detection_review/analysis.json), [accounting](../artifacts/png_context_detection_review/accounting.json), [coverage](../artifacts/png_context_detection_review/coverage.json).
- The figure preview was visually inspected at publication proportions; labels, markers, intervals and legend are unclipped. The actual LaTeX table compiled successfully at manuscript width and was visually inspected; no overfull/underfull warnings occurred. Temporary table preview files are not new research outputs.

CPU analysis/export on the execution host, including its retained local ledgers: `python -B scripts/analyze_png_context_detection.py`. Do not use that export command in a public-only checkout; the public verifier instead recomputes/checks the statistical analysis from saved evidence without private ledgers. Public saved-evidence verification: `python -B scripts/analyze_png_context_detection.py --verify`. Focused checks: `python -B -m unittest tests.test_png_observer -v`. The [review index](../artifacts/png_context_detection_review/README.md) separates these from the budgeted CUDA execution command and its local model/context prerequisites.

This is a controlled comparison of one alternate row, one model/checkpoint, two predefined scores and 20 groups. It does not isolate every property of conditioning (including the rows' different image statistics), test adaptive context inference, establish fully blind/model-independent detection, show resistance to arbitrary observers or provide cryptographic secrecy. Intervals are exploratory, not a universal-reliability, equivalence or family-wise significance claim. Near-chance A1 results remain inconclusive rather than evidence of security. No extra experiments, carrier generation, manuscript expansion, commit, push or publication followed the result.
