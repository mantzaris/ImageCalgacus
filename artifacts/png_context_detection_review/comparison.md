| Method | Score | Row1 AUC [95% CI] | Row2 AUC [95% CI] | Paired difference [95% CI] | Stego / unique controls |
|---|---|---|---|---|---|
| Fixed rank | Mean surprisal | 0.885 [0.743, 0.985] | 0.698 [0.515, 0.870] | -0.188 [-0.277, -0.100] | 20 / 20 |
| Fixed rank | Mean log2 rank | 0.840 [0.682, 0.965] | 0.662 [0.472, 0.848] | -0.177 [-0.280, -0.095] | 20 / 20 |
| Entropy gated | Mean surprisal | 0.830 [0.700, 0.938] | 0.748 [0.607, 0.882] | -0.082 [-0.162, 0.010] | 20 / 20 |
| Entropy gated | Mean log2 rank | 0.770 [0.630, 0.897] | 0.723 [0.578, 0.868] | -0.047 [-0.130, 0.037] | 20 / 20 |
| Arithmetic A1 | Mean surprisal | 0.557 [0.375, 0.743] | 0.593 [0.412, 0.772] | 0.035 [-0.022, 0.105] | 20 / 20 |
| Arithmetic A1 | Mean log2 rank | 0.575 [0.405, 0.758] | 0.598 [0.417, 0.773] | 0.023 [-0.032, 0.073] | 20 / 20 |

Difference = row2 minus row1. Higher scores always indicate stego. Paired length-stratified payload-group bootstrap, 2,000 replicates; 20 groups, not 60 independent controls. Row1 values and intervals are reused from accepted V2 evidence. No classification threshold is fitted.
