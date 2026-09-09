# GPU performance checkpoint

## Result

Optional **CUDA graph replay of the unchanged PixelCNN++ forward** reduced mean fresh-process fixed-rank encoding/decoding latency from **88.95 / 88.87 seconds to 17.36 / 17.28 seconds**. The matched encode-plus-decode speedup is **5.133×**. Useful throughput, counting only exactly recovered source bytes and both processes, increased from **0.480 to 2.463 bytes/second** across the three development payloads and their timing repetitions.

All **11 matched comparisons** passed exact equivalence, and all **22 saved PNG carriers** recovered exactly through fresh receiver processes. Eligible IDs, rank ordering and the exact float64 probabilities supplied to the coders matched across all 2,976 channel positions, including completion. Delivered PNG bytes, recovered source bytes, packet stopping and completion/authentication outcomes matched. Repeated timings also retained identical carrier/probability streams. No tolerance, repair, reroll, retry or protocol change was used. No benchmark model job failed.

Retain `--image-execution cuda_graph` as an explicit opt-in for this verified environment. **Reference execution remains the default.** This is an engineering benchmark on development cases, not another prospective study or a condition for accepting V2. Historical V2 outcomes and timings are unchanged.

[The comparison table](../artifacts/gpu_performance_review/comparison_table.md) reports each payload/method; [timings.csv](../artifacts/gpu_performance_review/timings.csv) contains every repetition. Fixed-rank comparisons have three repetitions per payload; gated and A1 each have one T1 comparison. Individual paired speedups range from 5.079× to 5.208×. These repetitions are not independent scientific observations; no inferential performance interval or broad hardware-speed claim is made.

## What changed, and what did not

The checkout started clean at accepted revision `5178dabfed42f8740366f6bb0a12d1070554735e`, with no subsequent commits. The execution package hash is `b5e2a8f2c2e39276feeb08ee4ed2fd4f294563237e76e1537f04eb4566d0c71b`; the final pre-model manifest hash is `851e82fe274ee647f2fb700150486cf3fc3604c6294837c92db08a5b9113f0ee`. Exact file identities are in the [execution freeze](../artifacts/gpu_performance_review/execution_identity.json). Reporting/test changes outside the frozen model package are identified separately. No frozen execution file changed during the benchmark.

Only one optimization candidate was implemented and measured:

- `ImageBackend._prepare_graph`: three warmup forwards on a side stream, then capture the existing `PixelCNN.forward` into `torch.cuda.CUDAGraph`, retaining input/output addresses.
- `_graph_forward`: the reference's exact NumPy float32 normalization/layout, copy into the persistent CUDA input, replay, and synchronize before timing or reading output. Timing events are reused. The selected parameters are still copied to CPU float64 before unchanged RGB conditioning and mixture-posterior updates.
- `forward`: explicit optional dispatch; its remaining reference body was AST-compared with `5178dab` and is identical. There is no second model implementation, custom kernel, reduced precision, removed weight-normalization operation or fallback.
- Output-only `DistributionDigest` fingerprints the ordered, length-framed ID/probability/rank streams. It does not supply state to either coder. Both benchmark modes use this same instrumentation; it is optional outside the benchmark.

The pattern uses the installed PyTorch 2.5.1 API and its side-stream/static-buffer requirements, not a new inference framework. See [PyTorch CUDA graph semantics](https://docs.pytorch.org/docs/main/notes/cuda.html#cuda-graphs); the installed `torch/cuda/graphs.py` was inspected before use. The short charged probe compared all float32 bytes of nine complete 100×32×32 network outputs per mode. All matched. Mean measured forward latency was 112.440 ms reference versus 12.447 ms graph (9.03×), but that short sequential probe includes first-forward effects and is **not** the headline end-to-end estimate. Graph setup and all probe loading/teardown were charged.

Sender and receiver gain only explicit image execution/audit options. Public scientific profiles are byte-unchanged; the mode is execution configuration, not payload metadata. Receivers still read exactly their own carrier/profile/row/key directory, after sender exit. Source and packet checks remain sender/evaluator-side. The runner reuses existing binding, receiver-boundary, evaluator and occupied-process accounting helpers; it creates no qualification credits or new scheduler.

The 292-byte packet, retained encryption, all coders, thresholds, raster/RGB order, model weights, precision, conditioning row, full PNG completion and serialization remain unchanged. Every delivered PNG is 32×31 RGB8 (992 pixels, 2,976 channel values); the model's shared first row is not delivered. Text inference/filtering code is untouched.

## Frozen cases and observed GPU execution

Selection was the lowest numeric development text ID in each of the 32–64, 65–96 and 97–128-byte bands: **T1 (32 B), T4 (96 B), T5 (128 B)**, all under existing row1. These are benchmark length bands, not a change to the source allocation. Original private packets/keys were verified against the frozen sources before model jobs; no new encryption occurred. T1 covered fixed, gated and A1; T4/T5 covered fixed. Two additional fixed timing repetitions ran only after the five initial comparisons passed, reversing each pair's order between repetitions. The manifest was finalized before the first model job.

Reference r0 carriers for all five payload/method combinations also equal their accepted V1 development carrier bytes; their historical execution identities were not relabeled. Benchmark execution IDs distinguish modes/repetitions; inherited development work fields are provenance only. Nothing was added to qualification or V2 observation counts.

All **45 charged model processes**—one short probe and 44 fresh sender/receiver jobs—recorded strict checkpoint loading, CUDA parameter/input/output placement, evaluation/inference mode, allocation on the selected UUID, positive process-specific activity and positive CUDA event intervals. Jobs ran serially; no active model process remained afterward.

The existing RankCloak image interpreter was reused: Python 3.10.13, PyTorch **2.5.1+cu124**, CUDA runtime 12.4, cuDNN 90100; no installation or checkpoint acquisition was performed. Hardware was **NVIDIA RTX 5000 Ada**, UUID `GPU-10d1f16f-9e79-08bb-b2ba-3353c04422cf`, PCI `00000000:09:00.0`, physical GPU 1 mapped to logical CUDA 0, driver 590.48.01. Checkpoint SHA-256 remains `a5ed558f6d4098ce3cbfd47658b7e3be37fae77b71a90c8a56f46a6266ff833f`.

RankCloak revision `ce853d42d6ba64065cb63c6bdfc0d825c62734cd` README, generation requirements and loader/replay settings were inspected. Existing attribution/licenses remain in [THIRD_PARTY.md](../THIRD_PARTY.md). Launch blocking, deterministic algorithms, disabled TF32 and the cuBLAS workspace setting remain unchanged. GGML graph/fusion controls still apply to the unchanged text backend; enabling this explicit **PyTorch image** graph does not enable llama.cpp graphs. Text's full-offload profile and reset/incremental-replay controls remain intact; no new text-model job ran.

## Timing interpretation and memory

Headline latency is child-process launch-to-exit, including imports, model hashing/loading, graph setup, occupied CPU work, serialization and teardown. Wrapper monitoring joins and the separate CPU evaluator are outside this established charge. Cold loading denotes fresh-process checkpoint/model initialization, not an intentionally evicted filesystem cache.

For the nine fixed timing pairs per mode:

| Nested measurement, mean per encode+decode pair | Reference | CUDA graph |
|---|---:|---:|
| Charged fresh-process latency | 177.819 s | 34.642 s |
| Encode + decode phases | 170.184 s | 25.829 s |
| CUDA-event forward intervals, inside those phases | 165.431 s | 21.251 s |
| Remaining phase time | 4.753 s | 4.579 s |
| Cold model loading | 1.876 s | 1.884 s |
| Graph setup | 0 | 1.174 s |
| Other occupied time, including imports/hash/teardown | 5.758 s | 5.755 s |

Do **not** add nested CUDA intervals to phase/process charges again. Events are recorded around forward execution and read after CUDA synchronization. Reference event intervals include device-idle gaps between host kernel launches; they are not a profiler sum of active kernel durations. Identical outputs plus shorter intervals and higher sampled activity are consistent with reduced launch/execution overhead, not fewer model operations or a changed likelihood calculation.

Peak PyTorch allocated memory was **484.479 → 473.849 MiB**, but allocator **reserved memory increased from 516 to 744 MiB**. Sampled process GPU memory peaked at **912 → 1,176 MiB**, including allocations outside PyTorch. These are different memory measures, not additive terms.

The existing wrapper repeatedly ran `nvidia-smi pmon -c 1 -s um`, matching the model PID. Across the 22 full jobs per mode, 10,019 reference and 1,637 graph samples with numeric SM readings were available; mean polling intervals were approximately 0.192/0.190 s. Mean sampled SM readings were 14.99%/73.31%, maxima 41%/82%. Driver counter windows, repeated/correlated samples and allocation-only observation gaps limit interpretation: neither a peak nor these descriptive sampled means establishes sustained utilization. Individual samples and job summaries are retained in [gpu_jobs.json](../artifacts/gpu_performance_review/gpu_jobs.json).

## Accounting, verification and limitations

The idempotent `gpu_performance` authorization is an absolute **7,200 seconds**. Existing phase caps remain V0 7,200, V1 50,400 and V2 54,000 seconds; no unused allowance was transferred. Both the benchmark and 144,000-second whole-project cap are enforced, with 140-second sender/receiver limits and a 180-second probe limit. The original conservative bound was 6,340 seconds, including complete paired recovery.

Actual benchmark use was **2,351.732528 seconds (0.65326 hours)**, including the **6.761419-second probe**, all loading, setup and teardown. Remaining benchmark allowance is **4,848.267472 seconds**. Historical V0/V1/V2 use remains **85,183.689935 seconds**; cumulative actual use is **87,535.422463 seconds (24.31540 hours)**, leaving **56,464.577537 seconds** below the whole-project cap. The established single 25% planning reserve gives **109,419.278079 seconds (30.39424 hours)** including history. It is unused forecast cushion, not another charge or permission for experiments. No work remains in this benchmark allocation.

Focused pre-model guards passed 5/5. The existing routine CPU suite ran **once after GPU completion: 79/79 passed in 11.671 s**, including six focused benchmark guards, retained source-cache/private integration and the model-free Linux process guard. No tests skipped on this execution host. This is not a new public-checkout portability campaign. [CPU evidence](../artifacts/gpu_performance_review/cpu_verification.json) distinguishes scopes. The public benchmark verifier reconciles all 22 saved outcomes and 11 comparisons without keys or inference; authentication is verified historical receiver evidence, not repeated by that CPU command.

All **10,465 protected historical artifact/run/log files** remained byte-identical, including original carriers, failures, retained keys/packets and ledgers. Public export is allowlisted and scanned for raw/hex/base64 key and packet material; it excludes weights, environments and private audit traces. Every benchmark carrier is retained. V2 is complete and accepted independently of this result.

The image speedup is established only for these development cases, pinned stack/device and fixed dimensions. Gated/A1 timing coverage is only one payload each. The reference path remains available. Existing V2 text filtering consumed approximately **70.6%, 75.1%, 88.8%** of encoding phases for fixed/gated/A1 respectively; those are old measurements, not new text benchmarks. Faster image GPU execution does not resolve that separate bottleneck or arithmetic text's information deficit under the frozen token cap. No security, naturalness, broad robustness or publication-level statistical claim follows.

## Reproduction and checkpoint boundary

Actual orchestration used the existing image/control interpreter (full command paths are in the GPU job records):

~~~sh
python -B -m imagecalgacus.gpu_performance --run runs/gpu-performance-001 --prepare-only
python -B -m imagecalgacus.runtime --stage gpu_performance --label cuda-graph-probe --max-seconds 180 -- python -B -m imagecalgacus.gpu_performance --run runs/gpu-performance-001 --probe
python -B -m imagecalgacus.gpu_performance --run runs/gpu-performance-001
python -B scripts/collect_gpu_performance.py --run runs/gpu-performance-001
~~~

The dedicated runner uses retained original packets; completed comparison records are not regenerated. Standalone image sender/receiver interfaces are unchanged except for optional `--image-execution cuda_graph --image-distribution-audit`, with each model command wrapped in the named budget stage. Exact artifact/packet/key paths and execution order appear in `gpu_jobs.json`; private material is not exported. Do not launch new repetitions beyond this manifest.

Public, CPU-only verification and timing-table reproduction:

~~~sh
python -B scripts/collect_gpu_performance.py --verify-public
python -B scripts/collect_gpu_performance.py --analyze-public
~~~

The [review packet](../artifacts/gpu_performance_review/README.md) is the checkpoint handoff. Retain the optional graph path and the measured engineering result; no further experiment is needed for this checkpoint. No V2 rerun, extra concealment experiment, manuscript, commit, push or publication was performed.
