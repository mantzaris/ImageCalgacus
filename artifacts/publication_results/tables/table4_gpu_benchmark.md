# Matched reference versus CUDA graph benchmark

| Payload / method | Bytes / repeats | Reference encode / decode (s) | Graph encode / decode (s) | Pair speedup | Recovered B/s reference → graph | Equivalence |
|---|---|---|---|---|---|---|
| T1 / Fixed | 32 / 3 | 88.97 / 89.28 | 17.38 / 17.28 | 5.14× | 0.180 → 0.923 | Exact |
| T1 / Gated | 32 / 1 | 90.17 / 90.07 | 17.38 / 17.23 | 5.21× | 0.178 → 0.925 | Exact |
| T1 / A1 | 32 / 1 | 91.83 / 91.03 | 17.83 / 17.28 | 5.21× | 0.175 → 0.911 | Exact |
| T4 / Fixed | 96 / 3 | 89.12 / 89.09 | 17.34 / 17.29 | 5.15× | 0.539 → 2.772 | Exact |
| T5 / Fixed | 128 / 3 | 88.76 / 88.24 | 17.36 / 17.27 | 5.11× | 0.723 → 3.696 | Exact |

Three development payloads, row1; timing repetitions are not new independent research observations. Fixed has three matched repetitions per payload; gated/A1 each have one T1 comparison. Latencies are means of full charged fresh processes, including loading, graph setup and teardown. Speedup is the ratio of matched mean charged pair times; per-row throughput is the accepted mean of individual exact-source-bytes/pair-second ratios (the Figure 4 pooled headline instead divides summed bytes by summed times). All 11 comparisons/22 recoveries match exact ID/order/probability stream hashes, PNG file bytes and recovered source bytes. Peak PyTorch allocated memory: 484.479 → 473.849 MiB; reserved: 516 → 744 MiB; sampled process maximum: 912 → 1,176 MiB. These are distinct, overlapping measures, not additive; per-combination measurements and nested CUDA-event/loading times are in the full-precision CSV. Tested RTX 5000 Ada, PyTorch 2.5.1+cu124 and unchanged checkpoint/float32 precision; no cross-hardware performance claim.
