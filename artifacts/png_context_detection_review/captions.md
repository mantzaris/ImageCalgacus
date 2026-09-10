# Figure and table captions

## Figure: PNG detectability with correct and mismatched conditioning

**A:** AUC of whole-carrier mean eligible-distribution surprisal under the correct row1 context (circles) and the previously frozen, payload-independent row2 context (diamonds). **B:** Paired AUC change, row2 minus row1. The same saved 60 V2 stego PNGs and 20 independent ordinary PNG controls are used in both conditions; the controls are shared across the three methods within each of 20 payload groups. Correct-context scores are reused from accepted V2 evidence. New observations score all 2,976 delivered RGB channels with the unchanged PixelCNN++ CUDA graph backend; no carrier is regenerated. Error bars are 95% percentile intervals from 2,000 length-stratified payload-group bootstrap draws, jointly preserving observer conditions, methods and shared controls. Higher scores always mean stego; AUCs are not reversed. Dotted lines mark AUC 0.5 and zero change, not fitted classification thresholds. The observer knows the exact model and scoring procedure but uses one alternate conditioning row. These exploratory, small-sample intervals neither establish equivalence nor imply security when they include chance.

Source: [analysis.json](analysis.json), [results.jsonl](results.jsonl), [frozen manifest](manifest.json). Formats: [PDF](context_auc.pdf), [SVG](context_auc.svg), [PNG](context_auc.png).

## Table: Paired PNG observer-context comparison

Correct-context AUCs and accepted grouped 95% intervals are compared with mismatched-context AUCs and paired changes for the frozen primary mean-surprisal and secondary mean-log2-rank scores. Both scores come from the same inference pass; their orientations remain higher-is-stego. Every method has 20 source payload groups, not 60 independent control pairs. Each group's ordinary PNG is used once under each context and shared across methods. Interval construction and failure handling are fixed in the manifest. The CSV retains unrounded values; manuscript displays round only at presentation. These are detection-score measurements on previously generated PNGs, not new payload-recovery observations.

Formats: [CSV](comparison.csv), [Markdown](comparison.md), [LaTeX](comparison.tex).
