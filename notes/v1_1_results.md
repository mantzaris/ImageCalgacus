# V1.1: arithmetic diagnosis and feasible next allocation

8 September 2026. **The two arithmetic text failures are well-supported capacity failures under unchanged A1, not observed stagnation, desynchronization or final-bit failure.** V1.1 diagnosis is complete; V1 is still not fully qualified. No held-out generation or V2 work occurred.

## Starting point and preservation

Started from clean commit `1b2379b5ac0ee104016a344e48de60b390ad0f69`, package hash `dd99e932b5b89b5def365cbb46f5dbe227abcb7d3f5cdb9e613a02c940cb47a3`. No applicable AGENTS.md was found in the repository or checked ancestors. Read both plans, accepted V1 notes/review files, implementation, tests and retained receiver logs.

All **700 protected files**, including 297 public V0/V1 review files and 51 retained key copies, match their initial hashes. The original 3,054,042-byte V1 ledger prefix is unchanged; two diagnostic jobs were appended to that same ledger. V0's historical 3,163.653124 seconds are unchanged. Nothing is superseded. [Preservation evidence](../artifacts/v1_1_review/preservation.json).

Only `receiver.py` changed within the application package: an opt-in observer copies A1 state **after** the existing consume operation. The ordinary path is unchanged. Detailed JSONL traces are exclusive-create, mode 0600, confined to ignored `.runtime/`, outside receiver inputs. They contain interval bounds/emitted bits and are deliberately private. A small CPU audit script and three focused tests were added; the existing projection script now accepts allocation/output arguments and refuses to overwrite accepted review packets or existing outputs. No coder, packet, backend, profile, context, sampling or serialization rule changed. Diagnostic package hash: `ea7857902e3a127f2ef014f907dc41a775290142ef9ff5e6ac27fa574442638c`. [Source identities](../artifacts/v1_1_review/source_manifest.json).

RankCloak remains pinned at `ce853d42d6ba64065cb63c6bdfc0d825c62734cd`. Its loading, CUDA-library preload, full reset, incremental evaluation and exact-byte adaptations remain intact; no new upstream source was copied. Models, weights, environments and licensing/attribution files were not changed.

## Arithmetic diagnosis

The published methodological comparator remains [Ziegler, Deng and Rush (2019)](https://aclanthology.org/D19-1115/). Re-inspected the pinned [reference arithmetic.py](https://github.com/harvardnlp/NeuralSteganography/blob/14e982564aeaf9a33f7b4de440deda2184d17f12/arithmetic.py), including integer partitions, common-prefix rescaling and its decoder's last-token endpoint emission. Project A1 explicitly replaces that last-artifact shortcut with known-length common-prefix stopping and validated zero extension. It is an independently implemented framing adaptation, not a bit-identical reproduction or a new arithmetic method. Source reuse permission remains unresolved; no reference code was copied.

Original reports gave matching sender/receiver bit counts, approximately matching accumulated surprisal and no zero-extension processing. They did **not** establish minimum interval width or absence of localized collapse. Two saved-carrier replays closed that specific gap; no prompt, seed, temperature, packet, token-cap or success search occurred.

Each receiver was freshly launched after the original sender had exited, with exactly its original carrier/profile/prompt/key directory. It received no packet, source, source digest, evaluator manifest, IDs, ranks or sender cache. The new trace is an **output**, not an input. Only after receiver exit did the separate CPU audit read the retained sender packet and compare its prefix/selection windows with the observed receiver stream. This proves prefix equality, not authenticated full-payload equality.

| Diagnostic, over all 2,048 tokens | I1 arithmetic | I5 arithmetic |
| --- | ---: | ---: |
| Recovered / required bits | 1,450 / 2,336 | 771 / 2,336 |
| Eligible-distribution surprisal, bits | 1451.382177 | 771.173525 |
| Accumulated eligible entropy, bits | 1493.857376 | 766.662506 |
| Quantized selected-symbol surprisal, bits | 1451.377565 | 771.160115 |
| Minimum interval width (integer units) | 5,045,674 | 37,150 |
| Final interval width | 1,652,994,276 | 3,843,796,398 |
| Minimum quantized support | 2 | 3 |
| Minimum retained eligible mass | 0.999504040 | 0.999050196 |
| Zero-bit steps | 1,662 | 1,847 |
| Longest zero-bit run, inclusive positions | 432; 1557–1988 | 517; 1153–1669 |
| Steps narrowing before rescaling | 2,048 | 2,048 |
| Single-bin collapse / unchanged zero-bit interval steps | 0 / 0 | 0 / 0 |
| Zero-extension or termination reached | No | No |

Every observed partition/CDF matched a separately written scalar check (Python nearest/even rounding and independently summed probabilities). Every interval and emitted bit matched the existing Fraction/iterative-half oracle, which does not use the coder's XOR/shift implementation. The entire recovered prefix and the source-window selection at **every** observed symbol matched the immutable original packet. Original aggregate probability/coder diagnostics and bit counts were reproduced exactly. [Compact data and 128-position checkpoints](../artifacts/v1_1_review/arithmetic_diagnosis.json).

For selected quantized probability `p*=bin_width/R_before`, the exact interval-accounting identity is:

`Σ −log2(p*) = emitted_bits + log2(2^32/R_final)`.

The final un-emitted interval information is only **1.377565 / 0.160115 bits** (identity residual below 6e-12 bits), not the missing 886 / 1,565 bits. Quantization changed accumulated selected surprisal relative to eligible q by only −0.004612 / −0.013410 bits. Rescaling can expand numerical width; diagnosis therefore tests narrowing **before** rescaling, not monotonicity of rescaled widths. Long zero-bit runs still narrowed on every step.

| Explanation | Evidence-supported assessment for both carriers |
| --- | --- |
| Low trajectory information rate | Strong direct support: the selected-symbol information is far below 2,336 bits at the fixed cap. This is trajectory-specific, not a universal language-model capacity bound. |
| Finite-precision collapse/stagnation | Not observed at any replayed position. Support remains multiple-valued and every step narrows; small quantization distortion cannot explain the missing bits. |
| Sender/receiver synchronization or implementation error | No error found: identical old/new aggregate diagnostics/progress, independent partition/interval checks, correct original-packet prefix and source-window selection at all 4,096 positions. This is bounded evidence, not proof for all possible inputs/runtimes. |
| Finite-message termination | Not reached. Neither receiver enters zero-extension lookahead, suffix validation or packet authentication. A final flush cannot supply hundreds of absent information bits. |

Both retain `packet_complete=false`, `carrier_complete=false`, `authenticated=false`, failure stage `capacity`, exit 2; neither produced recovered payload bytes. Exit 2 is the expected replay of a valid failed observation, not a diagnostic implementation failure.

The separate A1 width-three vector remains an **algorithmic limitation of this adaptation**: interval `[2^31−2,2^31+1)` with uniform-32 q collapses to one width-three bin after specified rounding/overflow handling and can stagnate indefinitely. Existing and new independent tests reproduce it. It did not affect these carriers. No bug fix, evidence supersession or arithmetic amendment is justified by these findings. Changing underflow handling, partitioning, precision or framing would require a separately reviewed algorithm amendment and renewed independent finite-stream/termination and artifact checks; it is not necessary to acknowledge these capacity failures and was not undertaken.

## Verification and GPU accounting

**44 CPU tests pass**: the original 41 plus focused narrowing-versus-stagnation, full-chain width-three stagnation, and corrupted-trace/wrong-source rejection checks. The original exhaustive small-interval, finite-message, suffix, truncation, packet, tokenization and pixel oracles remain. Packaged suite: 7.554 seconds; [test log](../artifacts/v1_1_review/cpu_tests.txt). The separate full-trace CPU audit passed all checks for both carriers.

Read-only final validation again returns V0 allocation complete, 10/10 exact; V1 allocation complete, ten exact and two recorded failures. V1 strict validation exits 1; complete-with-failures mode exits 0 without claiming all recovered. [Revalidation](../artifacts/v1_1_review/revalidation.json).

Both new jobs use the original Llama GGUF hash `86c8ea6c8b755687d0b723176fcd0b2411ef80533d23e2a5030f845d13ab2db7`, llama-cpp-python 0.3.23 and RTX 5000 Ada UUID `GPU-10d1f16f-9e79-08bb-b2ba-3353c04422cf`, physical 1 → logical CUDA 0. Full requested offload `n_gpu_layers=-1` is verified as **33/33 eligible layers**, with model/KV GPU allocation and process-specific GPU activity (sampled maximum SM utilization 97% in each process). The approved batch/microbatch=1, reset/incremental, graph/fusion/float32/workspace and complete-prefix controls are unchanged. No CPU/partial-offload retry. Image inference was not needed or rerun; its accepted strict CUDA evidence and pinned PixelCNN++ implementation remain unchanged, not newly verified here.

| Diagnostic job | Decode / filter s | Cold load s | Other process s | Charged s |
| --- | ---: | ---: | ---: | ---: |
| v1-033-v1-1-I1-arithmetic-diagnostic | 406.190 / 361.050 | 2.711 | 13.047 | 421.948 |
| v1-034-v1-1-I5-arithmetic-diagnostic | 396.360 / 351.014 | 2.650 | 13.624 | 412.634 |

Filtering is included in decode, not added again. Other process cost includes imports, model hashing, trace writing outside decode if any, and teardown. The wrapper charges the whole model process, including CPU processing while GPU resources are occupied. Jobs ran sequentially and exited. [Commands/GPU evidence](../artifacts/v1_1_review/gpu_jobs.json).

Preflight forecast: 833.689 seconds from the two original charged receiver runs, 1,042.112 with 25% headroom; separate hard timeout 550 seconds/job. Actual new charge **834.582 seconds**. No fresh V1.1 allowance was created.

| Accounting | Seconds |
| --- | ---: |
| Historical V0 | 3163.653 |
| Accepted V1 before this checkpoint | 4690.205 |
| This checkpoint's two diagnostic replays | 834.582 |
| Current V1 / original limit | 5524.787 / 7,200 |
| **Remaining V1 allowance** | **1675.213 (27.920 minutes)** |
| Cumulative whole-project actual charge | 8688.440 |

No extra pilot observations, encodings, nonces or keys were created. [Ledger summary](../artifacts/v1_1_review/budget.json).

## Authorized prospective amendment and forecast

Both plans now explicitly record **20 held-out images + 20 held-out texts, one existing context/direction, all three methods = 120 stego units**. Up to **40 independent ordinary traces** supply method-matched prefixes/full PNG controls within payload/context groups. A trace and its prefixes are not independent method replicates. Methods still share one immutable encrypted packet per group. Main contexts are the original first prompt/row, not a choice based on failure outcomes.

Keep the proposed corpora/preprocessing/exclusions: 20 held-out Fashion-MNIST images, two/class; 20 nonoverlapping unchanged Gutenberg spans, ten per existing UTF-8 length band. Actual corpus snapshots, provenance and disjointness are unfinished V1 work, not claimed prepared here. No easier selection, cap change, compression, packet-size change or new sampling policy is authorized. This is a **focused feasibility study**, not demonstrated publication-level power or broad reliability.

Recomputed directly from the twelve accepted pilot records and their charged jobs, including both failed arithmetic text attempts; only two observations/cell are available:

| Direction/method | Mean generate / replay s | Mean load + other process s | Charged pair s |
| --- | ---: | ---: | ---: |
| image-to-text/fixed | 48.019 / 48.003 | 5.349 + 26.181 | 127.552 |
| image-to-text/gated | 48.504 / 48.267 | 5.378 + 26.249 | 128.398 |
| image-to-text/arithmetic | 404.706 / 401.295 | 5.374 + 25.831 | 837.206 |
| text-to-image/fixed | 83.897 / 84.634 | 1.866 + 5.472 | 175.870 |
| text-to-image/gated | 84.281 / 84.367 | 1.942 + 5.650 | 176.240 |
| text-to-image/arithmetic | 84.442 / 84.124 | 1.832 + 5.609 | 176.008 |

Remaining development is **10.181 hours unreserved**, **12.727 with reserve** as a standalone planning view. Its unchanged 140 stego units comprise 38 sequence-check fixed text + 40 static-mask text + 38 fixed PNG + 6 per gated/arithmetic modality/method cell. Also retain 12 ordinary development/calibration traces and up to 46 development controls, with only the original qualifying pilot credits. Diagnostics receive no qualification-unit credit.

Development cost components: measured-cell extrapolation 19437.152 s; unmeasured static-mask proxy 5309.319 s; remaining ordinary calibration 1333.523 s; up-to-46 controls 10573.219 s. Static-mask cost uses the maximum measured sequence-check pair as a proxy, **not a measured upper bound**. Calibration/control counts retain the previous provisional modality balance; second-context timings are unmeasured. Preserve the current frozen thresholds/profile; further ordinary checks cannot be used to retune after stego failures.

| Whole-project forecast component | Unreserved hours |
| --- | ---: |
| Historical V0 + V1 + V1.1 actual usage | 2.413 |
| Remaining V1 qualification | 10.181 |
| Main stego generation, 120 units | 4.188 |
| Fresh-process main receiver replay | 4.171 |
| Main sender/receiver cold loading | 0.121 |
| Main other process/occupied CPU overhead | 0.528 |
| Up to 40 shared ordinary controls, including setup | 2.554 |
| Required 20 additional lossless PNG fresh receiver checks | 0.489 |
| Extra GPU scoring passes (already scored inline) | 0 |
| **Subtotal** | **24.645** |
| **One 25% reserve** | **6.161** |
| **Whole-project projection** | **30.806 / 40 hours** |

Formula: `1.25 × [actual history + remaining qualification + 20 × Σ_six_cells(generate + replay + cold load + process overhead) + 20 × (text_control + image_control) + 20 × mean_PNG_replay]`. All terms are unreserved. The reserve is applied once, conservatively also to spent history, and is not an actual charge. Do not insert the separately reserved 12.727-hour development figure into this formula.

The independently recomputed pre-diagnostic value is **30.516575 hours**; adding actual diagnostics with the same single reserve gives **30.806360 hours**, leaving 9.194 hours of forecast headroom. Main stego alone is 9.007 hours; main work including controls/lossless checks is 12.050 hours before reserve. [Machine-readable projection](../artifacts/v1_1_review/compute_projection.json).

These are conditional estimates, not confidence bounds or a guarantee. Arithmetic failures use measured cap-length costs, not successful fixed-rank throughput. Gated lengths, text-prefix filtering costs, other payload trajectories and the second development context can vary. Controls use one measured full text trace and one PNG trace; new controls are not guaranteed to cost the same. Loading and occupied CPU time are included, but CPU-only corpus preparation, PNG rewriting/pixel checks, UTF-8 roundtrips and aggregation require additional researcher/CPU time, not fabricated GPU measurements. Twenty extra PNG replays are budgeted once; ordinary artifact replay is already in each pair. No extra scoring job or optional sweep is hidden in zero additional GPU scoring.

The remaining phase allowance is only 0.465 hours. Full qualification would need about **12.261 additional V1-authorized hours beyond that balance** under the standalone reserved estimate. The 40-hour ceiling does not grant that authority; no larger allocation was launched.

## Exact remaining qualification conditions and next step

1. Finish and freeze development source/context manifests, provenance/terms, preprocessing/exclusion/disjointness checks; define held-out selection without generating held-out carriers.
2. Implement the singleton/static-mask comparison arm without altering the approved complete-prefix arm. Complete the existing 20-image × two-prompt 40-pair comparison (80 artifacts total); all 40 sequence-check fixed-rank artifact recoveries must pass. Two qualifying sequence-arm pilot units are credited; static arm failures remain visible.
3. Complete the 20-text × two-row fixed-image checks (40 total, two credited), retaining strict conditional RGB, PNG equality and fresh-process recovery. Freeze the second development row payload-independently.
4. Finish the unchanged 32 gated/arithmetic development timing units (eight per modality/method, two per cell credited). Reconcile capacity versus implementation failures, packet/carrier/authentication/equality statuses, and costs. Do not demand a rerolled full-size arithmetic text success; the complete arithmetic-text packet endpoint is still unobserved, and two diagnosed failures do not qualify the comparator broadly. Preserve A1's explicit finite-precision limitation and verify termination whenever it is actually reached.
5. Finish the remaining ordinary development checks/calibration evidence and matched development controls, with frozen current settings and no failure-driven tuning. Extend only the necessary existing runner/coverage checks to that fixed allocation, keeping same-packet pairing and independent receiver inputs.
6. Reconcile completed qualification and measured costs, then make an explicit protocol/compute freeze decision before any V2 authorization. The existing 20 lossless PNG replays plus raw UTF-8 roundtrips remain required before final study acceptance, separately budgeted above rather than falsely marked done.

No required qualification check was silently dropped. The smallest next engineering step is CPU-first preparation of those frozen manifests and the focused static-mask comparison arm; then a separately authorized, small paired development batch can replace its largest unmeasured cost assumption. Do not start the 120-unit main matrix yet.

## Executed commands and review boundary

The exact two budget-wrapper child argument vectors, GPU identities and measured costs are in gpu_jobs.json. Both used `--stage v1`, `--max-seconds 550`, and the normal receiver with `--private-arithmetic-trace .runtime/v1_1/diagnostics/<I1|I5>/trace.jsonl`. Original inbox paths and retained keys were reused for decoding only.

CPU commands executed from the repository root with the existing control interpreter:

    <control-python> -B -m unittest discover -s tests -v
    <control-python> -B scripts/diagnose_v1_arithmetic.py --output artifacts/v1_1_review/arithmetic_diagnosis.json
    <control-python> -B scripts/project_v1_compute.py --payloads 20 --contexts 1 --output artifacts/v1_1_review/compute_projection.json

The two reporting commands intentionally reject existing output files; use a new output path for an independent rerun. Exact read-only V0/V1 evaluator commands are in revalidation.json.

Critical review: no ground truth enters either receiver; bounds/emitted bits remain private; no saved-ID recovery, alternate termination, sampling/profile change, historical overwrite or extra experimental unit was introduced. Capacity and completion remain separate. The only scientific amendment is the explicitly authorized prospective allocation. No installations, weights, cloud resources, new algorithms/models, V2 runs, commits, pushes or publication occurred. V1.1 is a **completed diagnosis/proposal checkpoint**, not full V1 qualification.
