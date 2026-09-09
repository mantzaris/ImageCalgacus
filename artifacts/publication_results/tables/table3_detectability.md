# Exploratory known-model/context detectability

| Carrier / method | Frozen score | AUC [grouped 95% interval] | Scorable stego | Unique matched controls | Failed stego included |
|---|---|---|---|---|---|
| UTF-8 / Fixed | Mean surprisal | 1.0000 [1.0000, 1.0000] | 20 | 20 | 0 |
| UTF-8 / Fixed | Mean log2 rank | 1.0000 [1.0000, 1.0000] | 20 | 20 | 0 |
| UTF-8 / Gated | Mean surprisal | 1.0000 [1.0000, 1.0000] | 20 | 20 | 0 |
| UTF-8 / Gated | Mean log2 rank | 1.0000 [1.0000, 1.0000] | 20 | 20 | 0 |
| UTF-8 / A1 | Mean surprisal | 0.3800 [0.2600, 0.5025] | 20 | 20 | 20 |
| UTF-8 / A1 | Mean log2 rank | 0.3600 [0.2425, 0.4801] | 20 | 20 | 20 |
| PNG / Fixed | Mean surprisal | 0.8850 [0.7425, 0.9850] | 20 | 20 | 0 |
| PNG / Fixed | Mean log2 rank | 0.8400 [0.6825, 0.9650] | 20 | 20 | 0 |
| PNG / Gated | Mean surprisal | 0.8300 [0.7000, 0.9375] | 20 | 20 | 0 |
| PNG / Gated | Mean log2 rank | 0.7700 [0.6299, 0.8975] | 20 | 20 | 0 |
| PNG / A1 | Mean surprisal | 0.5575 [0.3750, 0.7426] | 20 | 20 | 0 |
| PNG / A1 | Mean log2 rank | 0.5750 [0.4050, 0.7576] | 20 | 20 | 0 |

Both frozen whole-carrier scores use higher-is-stego direction, including AUCs below 0.5. Intervals reuse the accepted 2,000-draw payload-group bootstrap with class/length strata and shared controls. There are 40 independent ordinary traces overall, not 120 per-method control replicates or 240 per-score observations. Each cell has 20 unique matched artifacts; no V2 duplicates or unscorable carriers were dropped. All 20 failed A1 text carriers are included. Small empirical perfect separation and a [1,1] bootstrap interval do not prove perfect population detection; near-chance scores do not prove security.
