# Publication results: figures and tables

CPU-only presentation of accepted evidence. **Four main figures, four main tables, two supplementary figures and one supplementary overhead table.** No new model inference, study-source selection, scoring pass or statistical fit. V1 development, V2 held-out outcomes and development GPU timing repetitions remain separate.

Built from checkout `5e08a8ba32136c0ec51e8d27b355e83ca956786a` (reviewed benchmark `5e08a8b`; no subsequent commit at start). New reporting code identities are separate from historical execution identities. [Captions](captions.md) · [LaTeX figure captions](captions.tex) · [Provenance and exact source hashes](data/provenance.json) · [Numerical checks/preservation](data/verification.json) · [Saved-evidence verification](data/public_evidence_verification.json).

## Main figures

### Actual bidirectional artifact transport

[PDF](figures/figure1_transport.pdf) · [SVG](figures/figure1_transport.svg) · [450-dpi PNG](figures/figure1_transport.png)

Exact canonical source bytes survived both delivered-file paths on these two predetermined examples.

First manifest-ordered fixed-rank V2 examples, HI1-prompt1-fixed and HT1-row1-fixed; selection did not use appearance. Images show unchanged saved pixels enlarged with nearest-neighbor interpolation and correct aspect ratios. A transports the canonical 16 × 16 grayscale array (256 bytes), not arbitrary original image-file bytes. Its literal leading text excerpt has display line wrapping only; the complete carrier is ../v2_review/cases/HI1-prompt1-fixed/carrier.txt. B transports all 63 literal UTF-8 bytes through a 32 × 31 RGB8 PNG; the native model canvas is 32 × 32, with the shared 1 × 32 RGB row withheld. Fresh receivers used only their own saved carrier, pinned profile/model, shared prompt1 or row1, and retained encryption key. Sources and their byte comparison were evaluator-only. Row1 is 96 shared context bytes, not transmitted payload. The full examples and exact source/recovery paths are linked in the index.

### Held-out recovery and exact useful rate

[PDF](figures/figure2_recovery_rate.pdf) · [SVG](figures/figure2_recovery_rate.svg) · [450-dpi PNG](figures/figure2_recovery_rate.png)

Fixed and gated methods recovered 20/20 in both directions; A1 recovered 20/20 through PNGs but 0/20 through text.

All six V2 cells, 20 held-out payload groups per direction. Recovery whiskers are the accepted two-sided 95% Clopper–Pearson intervals (Bernoulli working model); rate whiskers are the accepted 2,000-draw, stratified payload-group percentile intervals. These preserve class/length strata and paired methods. Points show cell means. Goodput is 8 × source bytes divided by every delivered symbol only when the complete carrier authenticates and exactly recovers; otherwise it is zero. All 20 A1 text failures remain in the denominator at zero goodput. Recovered packet prefixes are not useful delivery (Figure S1). Text axes use bits/token; PNG axes use bits/channel value, not bits/pixel (multiply the PNG rates by three). Zero-width rate intervals reflect identical observed rates, not universal reliability. The canonical-image and fixed-slot formats constrain these small-sample results.

### Exploratory whole-carrier surprisal distributions

[PDF](figures/figure3_detectability.pdf) · [SVG](figures/figure3_detectability.svg) · [450-dpi PNG](figures/figure3_detectability.png)

Rank-coded text separates strongly from ordinary text under this tested observer; PNG and failed A1 text show different, uncertain score distributions.

Each point is a saved V2 carrier or its matched ordinary control (20 of each per panel). Light connectors preserve payload-group pairing; horizontal offsets follow frozen group order only. Square open markers are ordinary controls; filled/colored symbols are stego, with crosses for failed A1 text transmissions. Scores are whole-carrier mean eligible-distribution surprisal under an observer who knows the exact model and shared context, without the encryption key. Each group owns one independent control trace; text methods reuse length-matched prefixes and PNG methods share the full ordinary PNG. Thus 120 method-specific links are only 40 independent traces across the study. No duplicate or unscorable V2 artifacts occurred. Annotations are the accepted higher-is-stego AUCs and 95% grouped intervals, never flipped when below 0.5. All failed delivered A1 text carriers remain scorable. Panel y-scales differ. Complete empirical separation in the small fixed/gated text sample, including its collapsed bootstrap interval, does not establish perfect population detection. AUC near 0.5 does not establish security against this or other observers.

### Behavior-preserving CUDA graph improvement

[PDF](figures/figure4_gpu_performance.pdf) · [SVG](figures/figure4_gpu_performance.svg) · [450-dpi PNG](figures/figure4_gpu_performance.png)

CUDA graph replay reduces matched end-to-end latency by about 5.13× without changing checked probability streams or carrier bytes, at greater reserved/process memory.

Development engineering benchmark, not V2: T1/T4/T5 contain 32/96/128 source bytes, all under row1. Fixed rank has three alternating-order matched timing repetitions per payload (nine comparisons). Colors identify execution mode and shapes repetitions; connectors in A/B join matched packets. Headline 5.133× speedup is the ratio of mean charged reference and graph encode-plus-decode time on the pinned RTX 5000 Ada / PyTorch 2.5.1+cu124 configuration. Charged fresh processes include imports, model hashing/loading, graph setup, CPU bookkeeping, serialization and teardown. Throughput is exactly recovered source bytes divided by both charged processes; the headline pools bytes and time across all nine repetitions, while C shows individual ratios. These are three development payloads, not nine independent research observations. All 11 benchmark comparisons (including single-payload gated/A1 in Table 4) had identical exact ID/order/probability stream hashes, delivered PNG bytes and recovered source bytes; all 22 recoveries passed. D shows maxima across fixed jobs separately for allocated tensors, reserved allocator storage and sampled process memory; they overlap and must not be added. Process memory is sampled, not a guaranteed true peak. No broad statistical speed claim or equivalence on other stacks is established; reference execution remains available.

## Supplementary figures

### Arithmetic information accumulation and carrier capacity

[PDF](figures/figureS1_arithmetic_capacity.pdf) · [SVG](figures/figureS1_arithmetic_capacity.svg) · [450-dpi PNG](figures/figureS1_arithmetic_capacity.png)

All 20 V2 A1 text and 20 A1 PNG cases, using retained audit observations every 128 consumed symbols and the final recorded endpoint. Dots are measured checkpoints; connecting segments are guides, not measured intermediate values. Axes have different carrier units and caps. Text stops at 2,048 tokens with 581–2,216 of the required 2,336 bits and never reaches zero-extension/termination; packet prefixes are not authenticated source delivery. PNGs reach the packet target before completing the remaining full 2,976-channel carrier. Curves stop at the packet endpoint; they do not extrapolate into ordinary completion. Useful packet-prefix bits are capped at 2,336; emitted zero suffix bits beyond that are kept separately in the supporting endpoint CSV and Table S1. Eligible surprisal and entropy checkpoint values are also in the data CSV, not invented from line segments. Isolated unchanged-interval steps in HI5/HI16 (failed text) and HT19 (successful PNG) were transient, longest run one; they do not establish sustained stagnation as the text-failure cause. Low accumulated information under the fixed cap remains the accepted explanation. A1 retains its separate, previously documented finite-precision stagnation limitation.

### Saved-text tokenization consistency: paired development evidence

[PDF](figures/figureS2_text_consistency.pdf) · [SVG](figures/figureS2_text_consistency.svg) · [450-dpi PNG](figures/figureS2_text_consistency.png)

V1 development comparison, separate from V2. Each column preserves one of 20 distinct canonical image payloads under both frozen prompts; 40 context-specific pairs are not 40 independent payloads. Within each pair, fixed-rank sequence and static arms transport the same immutable packet. Sequence eligibility checks the complete generated carrier prefix; static eligibility checks singleton tokens only, with the other filtering/coding rules held fixed. Static carriers were saved literally even when retokenization drifted; no repair, saved IDs or sender state reached receivers. Sequence recovered 20/20 under each prompt; static recovered 8/20 (forest) and 14/20 (soup), with 18 retained drift/replay failures. This motivates the tested main method’s saved-artifact consistency requirement, not a theorem that singleton filtering must always fail. The historical unavailable static matched-control prefix remains unavailable and is not scored or regenerated here.

## Tables

Each CSV retains unrounded numerical fields. Each LaTeX table is independently includable with `booktabs` and `array`; compiled PDFs/previews show the actual typeset layout at 7.1-inch table width, without shrinking text to fit.

| Item | Quick review | Manuscript | Numerical source |
|---|---|---|---|
| Experimental specification | [Markdown](tables/table1_specification.md), [preview](tables/table1_specification.png) | [LaTeX](tables/table1_specification.tex), [PDF](tables/table1_specification.pdf) | [CSV](tables/table1_specification.csv) |
| V2 recovery, useful rate and original runtime | [Markdown](tables/table2_v2_outcomes.md), [preview](tables/table2_v2_outcomes.png) | [LaTeX](tables/table2_v2_outcomes.tex), [PDF](tables/table2_v2_outcomes.pdf) | [CSV](tables/table2_v2_outcomes.csv) |
| Exploratory known-model/context detectability | [Markdown](tables/table3_detectability.md), [preview](tables/table3_detectability.png) | [LaTeX](tables/table3_detectability.tex), [PDF](tables/table3_detectability.pdf) | [CSV](tables/table3_detectability.csv) |
| Matched reference versus CUDA graph benchmark | [Markdown](tables/table4_gpu_benchmark.md), [preview](tables/table4_gpu_benchmark.png) | [LaTeX](tables/table4_gpu_benchmark.tex), [PDF](tables/table4_gpu_benchmark.pdf) | [CSV](tables/table4_gpu_benchmark.csv) |
| Framing, padding and carrier-position overhead | [Markdown](tables/tableS1_overhead.md), [preview](tables/tableS1_overhead.png) | [LaTeX](tables/tableS1_overhead.tex), [PDF](tables/tableS1_overhead.pdf) | [CSV](tables/tableS1_overhead.csv) |

## Complete saved examples behind Figure 1

| Direction | Source | Complete delivered carrier | Recovery |
|---|---|---|---|
| HI1 / prompt1 / fixed | [canonical PNG](../v2_review/cases/HI1-prompt1-fixed/source.png) | [complete UTF-8](../v2_review/cases/HI1-prompt1-fixed/carrier.txt) | [PNG](../v2_review/cases/HI1-prompt1-fixed/recovered.png), [raw pixels](../v2_review/cases/HI1-prompt1-fixed/recovered.gray) |
| HT1 / row1 / fixed | [literal UTF-8](../v2_review/cases/HT1-row1-fixed/source.txt) | [complete PNG](../v2_review/cases/HT1-row1-fixed/carrier.png) | [literal UTF-8](../v2_review/cases/HT1-row1-fixed/recovered.txt) |

The excerpt byte range and exact prefix are retained in [figure1_examples.json](data/figure1_examples.json) and [figure1_carrier_excerpt.txt](data/figure1_carrier_excerpt.txt). Display wrapping is not serialization. Public review folders contain source truth and are not receiver inboxes.

## Numerical definitions and limitations

All recovery/rate/AUC intervals are read unchanged from accepted V2 `analysis.json`. Recovery uses boundary-aware Clopper–Pearson; rate/AUC/paired continuous intervals use 2,000 PCG64 draws (seed 2026090901 plus direction offset), resampling whole payload groups within class/length strata. Methods and shared controls remain together. Twenty groups per direction are not a representative population sample. No additional significance test, sign selection or threshold fit is performed.

V2 has 120 outcomes and 40 independent ordinary controls, with 20 scorable stego and 20 unique matched controls per score cell. Failed A1 text carriers remain included. No V2 exact-control duplicates occur. The V1 unavailable historical static prefix remains unavailable; Figure S2 uses recovery only. [Full-precision plotted score pairs](data/detectability_observations.csv) and [accepted paired differences](data/accepted_paired_differences.json) retain dependencies.

GPU headline uses nine fixed comparisons per mode: 177.818629 → 34.641733 mean charged pair seconds; summed recovered bytes / summed pair times = 0.479890 → 2.463310 B/s. Table 4 uses the accepted mean individual throughput per payload/method; these estimands differ slightly before rounding. Full [timing rows](data/gpu_timing_observations.csv) preserve cold load, graph setup and nested CUDA events. CUDA events overlap phase/process time and are not extra charges or profiler-summed active kernel durations. Sampled process memory is not allocator reservation; none of the memory measures is additive.

The existing benchmark used repeated PID-matched `nvidia-smi pmon -c 1 -s um` observations (roughly 0.19 s polling). Driver windows, correlated samples and observation gaps prevent claims of sustained utilization. No fresh GPU queries or runs are needed for these exports. Text filtering remains a separate bottleneck; [fractions recomputed from retained V2 reports](data/text_filtering_limitation.json) are supporting timing evidence, not new benchmarks. Faster image inference does not correct arithmetic text information deficits.

New endpoint/memory displays are descriptive views of retained records, not new inference or statistical analyses. Arithmetic trajectories use only actual 128-position checkpoints and endpoints; packet bits are capped before suffix diagnostics. All six requested figures were supported by retained evidence.

## Claim-to-evidence limits

| Claim | Supported evidence | Not established |
|---|---|---|
| Bidirectional exact artifact recovery | Supported for the tested canonical payloads, pinned models and unchanged artifact symbols: fixed/gated 20/20 per direction; A1 PNG 20/20. Figures 1–2; Table 2; V2 source/carrier/recovered artifacts. | Not arbitrary original-image container recovery, general reliability, lossy robustness or security. |
| Complete-prefix consistency in the main text path | Supported design requirement for this evaluated implementation: sequence 40/40; singleton static 22/40 in paired V1 development. Figure S2; V1 static_pairs.json. | Not a universal impossibility theorem for other serializers; 20 payloads, not 40 independent payloads. |
| Arithmetic text capacity limitation | Observed 0/20 V2 packets by the fixed cap; low-information trajectories are the accepted diagnosis. Figure S1; Table 2; V2 arithmetic audits. | Partial packet information is not payload delivery; no universal termination guarantee for A1; no full text success established. |
| Observed detectability differences | Supported only for the frozen model/context-aware mean-surprisal and log-rank observer. Figure 3; Table 3; accepted grouped intervals. | Neither perfect population detection nor imperceptibility, unknown-detector resistance or secrecy is established. |
| Behavior-preserving GPU speedup | Matched fixed-rank charged latency improves 5.133×; 11 exact stream/carrier comparisons and 22 exact recoveries. Figure 4; Table 4; exact stream comparison records. | Three development payloads and pinned hardware/runtime; timing repeats are not extra independent study observations. |

## Reproduction and provenance

From the repository root, using Python with NumPy, Pillow and Matplotlib plus `pdflatex` (`booktabs`, `array`, `lmodern`, `caption`) and `pdftoppm`:

```sh
python -B scripts/build_publication_results.py
```

The existing compatible interpreter on this host is `/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python`. No dependency installation is part of this task. The entry point reads public saved evidence, performs focused numerical/identity assertions and the three public evidence verifiers, writes only this new output directory, compiles table previews, and checks that accepted artifacts and ledgers are unchanged. Private keys, prepared packets, weights, raw audit traces and environments are never inputs. If local ledgers exist, their balances/hashes are checked read-only; a public checkout instead reports the accepted historical accounting without claiming a local ledger audit.

Saved-evidence verifiers (CPU-only, no authentication replay):

```sh
python -B scripts/collect_v2_review.py --verify-public artifacts/v2_review
python -B scripts/collect_gpu_performance.py --verify-public
python -B scripts/finalize_v1_qualification.py --verify-public artifacts/v1_qualification_review
```

Preservation: 3,544 existing files verified byte-identical. No new GPU time charged: 0 s. Cumulative recorded use remains 87,535.422463 s; historical stage balances are in [verification.json](data/verification.json). No accepted V2/benchmark analysis or execution identity was overwritten.

Evidence roots: [V2](../v2_review/README.md), [GPU benchmark](../gpu_performance_review/README.md), [V1 qualification](../v1_qualification_review/README.md). Model/code/corpus attribution remains in [THIRD_PARTY.md](../../THIRD_PARTY.md) and the frozen source provenance. No generated substitute image, new dataset or model result is used. Supporting verification notes and visual review are in [notes/publication_results.md](../../notes/publication_results.md).
