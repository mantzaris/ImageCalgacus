# Descriptive PNG score shifts

| Category | Artifacts | Row1 mean | Row2 mean | Mean change | Median change |
|---|---:|---:|---:|---:|---:|
| Ordinary controls | 20 | 3.684 | 4.294 | +0.610 | +0.621 |
| Fixed rank | 20 | 4.191 | 4.525 | +0.334 | +0.286 |
| Entropy gated | 20 | 4.074 | 4.588 | +0.513 | +0.555 |
| Arithmetic A1 | 20 | 3.770 | 4.399 | +0.629 | +0.636 |

All score values use bits per delivered RGB channel value. Changes are within-artifact row2 minus row1. These are descriptive, post hoc means/medians, not AUC changes or new inferential results.

The mean fixed-rank-minus-control gap, paired within the original 20 groups, is **0.507624** under row1 and **0.231119** under row2: change **-0.276505**. Controls are counted once and shared across methods. Unrounded paired gaps are retained in the fixed-rank rows of the observations CSV.
