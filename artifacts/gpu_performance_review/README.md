# Development GPU performance benchmark

Optional PixelCNN++ **CUDA graph replay achieved a 5.133× matched end-to-end speedup**. Mean fixed-rank fresh-process encode/decode latency fell from **88.95 / 88.87 s to 17.36 / 17.28 s**; useful recovered-payload throughput increased from **0.480 to 2.463 B/s**, counting both processes.

**11/11 comparisons are exactly equivalent; 22/22 saved PNGs recovered exactly.** All per-position ID/probability/order stream hashes, carrier bytes and recovered source bytes match, including timing repetitions. All five initial reference carriers also match their accepted development originals. No model job failed or retried.

This is not V2 data: T1/T4/T5 are existing 32/96/128-byte development messages under row1. T1 covers fixed, gated and A1; T4/T5 cover fixed. Fixed has three timing repetitions per payload, with alternating execution order. There are no new independent study observations or qualification credits. Reference remains the default; graph mode is explicit opt-in for the verified stack/device.

Start with the [compact comparison table](comparison_table.md) and [full report](../../notes/gpu_performance.md). Individual measurements are in [timings.csv](timings.csv) and [timings.json](timings.json), including cold loading, graph setup, synchronized CUDA intervals and peak allocated/reserved memory. CUDA intervals are nested inside process time, not extra charges or sums of active kernel durations. Graph allocator reservation rises from 516 to 744 MiB. Sampled GPU activity is not a sustained-utilization guarantee.

Evidence:

- [Frozen manifest](manifest.json), [execution identity](execution_identity.json), [unchanged execution files](execution_identity_check.json).
- [22 outcomes](results.jsonl), [complete verification](public_verification.json), [example exact comparison](comparisons/T1-fixed-r0.json), [historical reference equality](historical_reference_equivalence.json). All 11 comparison records are retained under `comparisons/`.
- [Short exact-output probe](probe.json), [45 GPU process records and samples](gpu_jobs.json), [receiver boundaries](receiver_boundaries.json).
- [Accounting](accounting.json), [authorization](authorization.json), [historical preservation](preservation.json), [privacy checks](privacy.json), [file hashes](artifact_hashes.json), [79/79 local CPU checks](cpu_verification.json).
- T1 fixed example: [source](cases/T1-fixed-r0-cuda_graph/source.txt), [reference PNG](cases/T1-fixed-r0-reference/carrier.png), [graph PNG](cases/T1-fixed-r0-cuda_graph/carrier.png), [recovered text](cases/T1-fixed-r0-cuda_graph/recovered.txt). Every generated carrier/output is retained under `cases/`.

New charged use is **2,351.732528 s**, leaving **4,848.267472 s** of this separate 7,200-second allowance. Cumulative actual use is **87,535.422463 s**; the whole-project ceiling leaves **56,464.577537 s**. All prior caps/ledgers and 10,465 protected historical files are unchanged. No second optimization candidate, new text-model job, held-out carrier or V2 rerun occurred.

Public CPU verification and table reproduction (no keys, weights or neural inference):

~~~sh
python -B scripts/collect_gpu_performance.py --verify-public
python -B scripts/collect_gpu_performance.py --analyze-public
~~~

GPU execution used the retained RankCloak `.venv` interpreter, PyTorch 2.5.1+cu124 and RTX 5000 Ada, with original numerical settings. Full actual subprocess commands are in `gpu_jobs.json`; the dedicated entry point is `python -B -m imagecalgacus.gpu_performance --run runs/gpu-performance-001`. It requires private original packet bindings for pending work, never re-encrypts a pair, and does not repeat completed comparisons. This completed benchmark authorizes no extra repetitions.

Keys, packets, weights, environments and raw private traces are excluded. Public directories contain ground truth and are **not receiver inboxes**. Receivers actually saw only their own carrier/profile/row/key; execution-mode/audit flags supplied no sender diagnostics. Public verification checks saved evidence and source equality, not fresh cryptographic authentication or GPU replay.

Accepted [V2 results](../v2_review/README.md) are separate and unchanged. The image speedup does not resolve CPU text filtering or arithmetic text's information deficit. These few development cases establish neither portable equivalence on other GPU stacks nor broad performance/reliability claims.
