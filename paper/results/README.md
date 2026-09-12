# Manuscript results integration index

The [ICAART single-PDF index](../icaart2027/README.md) is the consolidated entry point. Reviewers are assumed to receive only the [12-page submission PDF](../icaart2027/ICAART2027_submission.pdf). Its method, experimental design, central results and limitations require no companion or repository access.

| Main location | Item | Supporting evidence remains separate |
|---|---|---|
| Page 3, Figure 1A–B | Actual image-to-text and text-to-generated-PNG transports | Same retained first fixed-rank cases, manuscript-only layout variant |
| Page 6, Figure 2A–C | Canonical photograph, delivered model-rank PNG, ×32 absolute difference, complete source/recovered text | Same BSDS 2018 example, no new carrier or pixel enhancement |
| Pages 9–10, Table 2/Figure 3 | All six prospective recovery, goodput and runtime cells | Original V2 evidence and timings unchanged |
| Page 11, Figure 4 | Correct/mismatched PNG observer AUC | Same 80 observations, not photograph detection |
| Page 11, Table 3 | Paired photograph recovery, fidelity and runtime | Model ranks versus simple parity, twenty held-out groups |
| Section 5.5 | Matched 5.13× CUDA graph result and exact equivalence | Three development payloads; detailed optional Figure S6/Table S6 |
| Sections 3–4 | Packet, context, coding, placement, data, GPU and inference boundaries | Compact details brought into the main PDF |
| Discussion | Sequence versus static development findings and lossless checks | Twenty distinct image payloads under two contexts, not forty independent payloads |

The [PNG context Methods/Results/limitations component](png_context_detection.md) is preserved. Main Section 5.4 includes the four descriptive score shifts and the fixed/control gap, without requiring companion Figure S5 or Tables S4–S5. Other optional companion material includes the process diagram, capacity checkpoints, full scores, overheads and first three photograph examples. Its supplementary-upload status remains unconfirmed.

Accepted [publication results](../../artifacts/publication_results/README.md), [photograph results](../../artifacts/cover_rank_v1_review/README.md) and all other review packets are unchanged. Only the manuscript variants are regenerated:

```sh
../llm-rankcloak/.venv/bin/python -B paper/icaart2027/build_submission_figures.py
python -B paper/icaart2027/build.py
python -B paper/icaart2027/package_source.py
```

Do not use older publication/addendum generators to reset manuscript numbering. Source figure provenance, independent ZIP compilation, numerical checks and visual inspection are linked from the ICAART index. Author-side rights, AI-disclosure and public-history decisions remain in [AUTHOR_REVIEW](../icaart2027/AUTHOR_REVIEW.md). This editorial operation uses zero additional GPU time and performs no venue submission.
