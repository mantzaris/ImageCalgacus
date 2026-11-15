# Claim-to-evidence map

This revision uses completed research only. `python3 paper-ICBDAIA/verify_evidence.py`
checks saved counts, cell means, AUC point estimates, timing ratios and equality
records without loading research modules or models. Its result and source hashes
are in [evidence_audit.json](evidence_audit.json). Accepted confidence intervals
are retained, not refitted. Public records document historical authentication;
this manuscript audit does not repeat private-key authentication or decoding.

## Main generated-carrier study

| Claim | Authoritative saved evidence | Boundary |
|---|---|---|
| 120 prospective outcomes, 100 exact successes and 20 retained capacity failures; 40 independent ordinary controls | [V2 results](../artifacts/v2_review/results.jsonl), [manifest](../artifacts/v2_review/manifest.json), [controls](../artifacts/v2_review/controls.json) | 20 payload/context groups per medium; three methods per group. The 120 control links do not create 120 independent controls. Text controls are matched prefixes of 20 ordinary traces. |
| Fixed and gated recover 20/20 in each direction; A1 recovers 20/20 PNGs and 0/20 text payloads | [Six-cell table](../artifacts/publication_results/tables/table2_v2_outcomes.csv), `exact_recovery` in V2 results | Exactness requires authenticated packet recovery and evaluator equality of source content, using a fresh receiver given saved carrier, declared profile/context and key. |
| Image exactness is the standardized 16×16 grayscale pixels; text exactness is literal UTF-8 bytes | [Specification](../artifacts/publication_results/tables/table1_specification.csv), [receiver boundaries](../artifacts/v2_review/receiver_boundaries.json), V2 `source_sha256`/`recovered_sha256` | Does not restore arbitrary original photo files, metadata, compression or color information. Sender token IDs, ranks, original source and sealed packet are excluded from receiver inputs. |
| 292-byte packet = 2,336 bits, including 36 framing/encryption bytes and 256-byte slot | [Overhead](../artifacts/publication_results/tables/tableS1_overhead.csv), V2 `packet_bytes`, `framing_bytes`, `slot_padding_bytes` | Held-out text is 58–128 bytes, mean 93.2; mean unused slot padding 162.8 bytes. The evaluation uses uncompressed fixed-size packets. |
| Fixed/gated/A1 exact text goodput is 3.324675/3.124640/0 bits per token; all PNG methods average 0.2505376344 bits per channel, or 0.7516129032 bits per pixel | Six-cell table, V2 `source_bytes`, `tokens`, `channels`, `exact_recovery` | Goodput is recovered source bits divided by full delivered carrier symbols, zero on failure. PNG has 32×31 RGB pixels, 2,976 channel values. The shared 32-pixel context row is not delivered. |
| Gating lowers text goodput by 0.200035 bits/token and raises charged pair time by 23.963806 s versus fixed | [Paired differences](../artifacts/v2_review/paired_differences.csv), [analysis](../artifacts/v2_review/analysis.json), `paired_differences` | Saved 95% intervals: goodput [−0.219237, −0.180526], time [20.337052, 27.583976] s. Same payload and packet paired across methods. |
| All text A1 outcomes hit the 2,048-token cap before completing 2,336 packet bits; recovered prefixes span 581–2,216 bits (mean 1,456.85) | [Arithmetic audits](../artifacts/v2_review/arithmetic_audits.json), V2 `failure_stage`, `packet_bits_recovered`; [endpoint table](../artifacts/publication_results/data/arithmetic_endpoints.csv) | All 40 arithmetic audit records pass saved interval/partition, prefix and source-window checks. No full-size arithmetic text recovery is observed; this is a finite-message implementation/allocation result, not a general impossibility claim. |
| Complete-prefix token filtering is needed for saved-text consistency | [Static/sequence pairs](../artifacts/publication_results/data/static_sequence_pairs.csv), [filtering limitation](../artifacts/publication_results/data/text_filtering_limitation.json), V2 `serialization` | Earlier development comparison: sequence 20/20 under each of two prompts; static 8/20 and 14/20. These are 20 distinct payloads reused across contexts, not 40 independent payloads. No tokenization drift is recorded for V2. |

Recovery intervals are the saved two-sided 95% Clopper–Pearson bounds:
20/20 → [0.8315665290, 1] and 0/20 → [0, 0.1684334710]. They are
Bernoulli working-model intervals for a small fixed, stratified allocation.
Continuous/paired and AUC intervals use the accepted 2,000 whole-group,
stratified bootstrap draws, retaining methods and shared controls together.
Equal-success paired binary cells also have conservative ±19.675968 percentage
point bounds; a collapsed empirical bootstrap interval is not certainty.

## Detection and observer context

| Claim | Saved evidence | Interpretation |
|---|---|---|
| Fixed and gated text completely separate from ordinary matched samples under both scores | [Detection table](../artifacts/publication_results/tables/table3_detectability.csv), [per-artifact scores](../artifacts/publication_results/data/detectability_observations.csv) | Both empirical AUCs are 1.0000. This materially limits concealment claims, without proving perfect population detection. |
| Text A1 primary/secondary AUCs are 0.3800/0.3600; PNG A1 primary AUC is 0.5575 | Same table and scores | All 20 failed text carriers remain included. Higher-is-stego orientation was frozen; values below 0.5 are not flipped. Near-chance scores do not demonstrate security or useful delivery. |
| Correct-row PNG primary AUCs fixed/gated/A1: 0.8850/0.8300/0.5575; mismatched row: 0.6975/0.7475/0.5925 | [Context comparison](../artifacts/png_context_detection_review/comparison.csv), [80 scored artifacts](../artifacts/png_context_detection_review/results.jsonl), [analysis](../artifacts/png_context_detection_review/analysis.json) | Same 60 stego PNGs and 20 controls; repeated scoring, no new transmissions. Observer knows exact model/procedure but uses one alternative, already frozen row. |
| Fixed primary AUC changes −0.1875 [−0.2775, −0.1000]; gated −0.0825 [−0.1625, 0.0100]; A1 +0.0350 [−0.0225, 0.1050] | Context comparison `difference`/`difference_ci_*` | Paired differences are row2−row1, with common group draws. A clear change for one method and uncertain change for another does not establish a difference in sensitivities. |
| Mean fixed/control score gap narrows from 0.507624 to 0.231119 bits/channel | [Descriptive addendum](../artifacts/png_context_detection_addendum/score_shift_summary.csv), [results prose](../paper/results/png_context_detection.md) | Post hoc descriptive arithmetic only. Row1 is generated-image context, row2 random RGB; this does not isolate correctness from row-statistic differences or prove the cause of AUC changes. |

Scores are whole-carrier mean eligible-distribution surprisal and mean log2 rank,
with known model/context and no fitted classifier. They do not assess arbitrary,
blind or model-independent observers, human naturalness, or photograph carriers.

## Cost and photograph extension

| Claim | Saved evidence | Boundary |
|---|---|---|
| Original charged pair means (s): text fixed 123.3261, gated 147.2899, A1 826.5660; PNG 178.1808, 178.5330, 179.0076 | [V2 job records](../artifacts/v2_review/gpu_jobs.json), six-cell table, V2 analysis | Launch-to-exit charges include failed attempts, loading, occupied CPU work, serialization and teardown. Encode/decode phases are nested subsets. |
| Matched development GPU speedup is 5.1330754991×, mean pair 177.8186288 → 34.6417326 s | [Timing analysis](../artifacts/gpu_performance_review/timings.json), [22 benchmark results](../artifacts/gpu_performance_review/results.jsonl), [comparison records](../artifacts/gpu_performance_review/comparisons/) | Ratio of pooled charged times for nine fixed pairs: T1/T4/T5, three repeats each. One extra gated and one A1 comparison make 11 comparisons and 22 exact recoveries. This is a separate development benchmark on RTX 5000 Ada/PyTorch 2.5.1+cu124, not replacement V2 timings or a universal speedup. |
| Benchmark modes preserve carrier/source bytes and exact eligible-ID/probability/rank-order stream digests | Benchmark results `distribution_digest`, comparison `equivalence.checks` | Checked historical output equivalence; CUDA graph reuse changes execution, not the scientific coder. CUDA-event intervals are nested and not extra charges. |
| Photograph model-rank and parity arms each recover 20/20 held-out messages | [Photograph results](../artifacts/cover_rank_v1_review/results.jsonl), [summary](../artifacts/cover_rank_v1_review/summary.csv), [manifest](../artifacts/cover_rank_v1_review/manifest.json) | Separate later study: six development and 20 held-out cover groups, two paired arms; 52 recoveries overall. Not an addition to V2's 120 outcomes. |
| Mean model/parity PSNR 70.254794/70.398374 dB; SSIM 0.9999664123/0.9999687999; pair runtime 13.881909/1.508575 s | Photograph summary; [paired summary](../artifacts/cover_rank_v1_review/paired_summary.json) | Descriptive means over the same 20 groups. Parity is slightly better in mean fidelity and substantially faster. Learned partitions show no demonstrated advantage here; parity is a simple comparator, not a state-of-the-art baseline. |
| Reconstructible coarse context preserves each channel's 4-value bin and requires no original photograph at receiver | [Photograph profile](../artifacts/cover_rank_v1_review/profile.json), [verification](../artifacts/cover_rank_v1_review/verification.json), [protocol report](../notes/cover_rank_v1_results.md) | The theoretical channel change bound is 3; observed maxima model/parity are 2/1. Fidelity and exact recovery do not establish low detectability or robustness to lossy edits. |

## Reconciled discrepancies and presentation traps

1. **Arithmetic failure labels:** inherited `verified_A1_stagnation_capacity`
   labels for HI5/HI16 are broader than the detailed audits. Those cases have
   respectively one and three isolated unchanged-interval steps, longest run one;
   successful HT19 PNG also has one. The manuscript follows the detailed records:
   capacity failure with insufficient accumulated information under the fixed cap,
   without claiming sustained stagnation caused these failures.
2. **Offered rate versus recovery:** legacy `useful_bits_per_*` can remain positive
   for failed text. Use `exact_goodput_bits_per_symbol` or its independently
   recomputed zero-on-failure definition. Partial packet prefixes are not delivery.
3. **Timing boundaries:** `sender_total_seconds`/`receiver_total_seconds` inside
   evaluation reports omit some wrapper-charged process time. All headline pair
   means use saved `gpu_jobs.json` charges or benchmark `charged_pair_seconds`,
   matching the accepted analyses. The 9.03× short forward probe is not the 5.13×
   end-to-end headline.
4. **Rounding:** some narrative tables round PNG A1 AUC 0.5575 to 0.558. Four
   decimals preserve the authoritative value and distinguish it from 0.557 or
   0.558 interpreted as exact. No underlying score discrepancy was found.
5. **Development versus held-out scope:** photograph 52/52 includes development;
   main held-out results are 20/20 per arm. Benchmark repetitions are timing
   repetitions on three development payloads, not additional held-out recovery
   observations. Context scores are repeated observations of existing PNGs.
6. **Rights and source exactness:** BSDS research distribution does not establish
   blanket photograph republication rights. See original
   [asset notices](../paper/icaart2027/ASSET_NOTICES.md) and
   [author review](../paper/icaart2027/AUTHOR_REVIEW.md). Canonical image recovery
   does not imply recovery of the original photograph/file or its publication rights.

No saved numerical inconsistency was found after these distinctions were applied.
The original manuscript, research code, saved evidence and declarations remain the
scientific record; this directory changes their presentation only.
