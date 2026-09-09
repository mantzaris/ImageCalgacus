# V2 recovery, useful rate and original runtime

| Carrier / method | Exact / attempted; 95% interval | Exact goodput; 95% interval | Encode phase (s) | Decode phase (s) | Charged pair (s) | Failure |
|---|---|---|---|---|---|---|
| UTF-8 / Fixed | 20/20<br>[83.16, 100.00]% | 3.3247<br>[3.3247, 3.3247] | 45.63 | 45.31 | 123.33 | None |
| UTF-8 / Gated | 20/20<br>[83.16, 100.00]% | 3.1246<br>[3.1054, 3.1441] | 57.31 | 57.30 | 147.29 | None |
| UTF-8 / A1 | 0/20<br>[0.00, 16.84]% | 0.0000<br>[0.0000, 0.0000] | 398.15 | 396.01 | 826.57 | Token-cap capacity |
| PNG / Fixed | 20/20<br>[83.16, 100.00]% | 0.2505<br>[0.2473, 0.2535] | 85.27 | 85.31 | 178.18 | None |
| PNG / Gated | 20/20<br>[83.16, 100.00]% | 0.2505<br>[0.2473, 0.2535] | 85.29 | 85.65 | 178.53 | None |
| PNG / A1 | 20/20<br>[83.16, 100.00]% | 0.2505<br>[0.2473, 0.2535] | 85.59 | 85.77 | 179.01 | None |

Original held-out V2 timings, including unsuccessful attempts; later graph timings are not substituted. Goodput units are bits/token for UTF-8 and bits/channel value for PNG; PNG rates multiply by three to obtain bits/pixel. Recovery uses accepted 95% Clopper–Pearson bounds; goodput uses accepted 2,000-draw stratified payload-group percentile intervals, n = 20 groups per direction. Incomplete/unauthenticated outcomes have zero exact goodput. Encode/decode phases exclude cold loading and other occupied time; the charged pair includes both full fresh processes, loading and teardown. These nested measurements are not additive charges. All 20 failures are A1 text capacity outcomes, with no authenticated payload.
