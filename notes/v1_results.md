# V1 implementation and bounded pilot results

V1 implementation and the initial 12-unit pilot are complete; **V1 is not fully qualified and V2 is not ready**. Ten payloads recovered exactly. Both arithmetic image-to-text attempts exhausted the fixed carrier budget, so successful arithmetic recovery in that direction remains unestablished. No V2 work, additional model family/context, dependency installation, weight download, cloud allocation, commit or push occurred.

## Starting point and preserved V0

Starting commit: `bc9e98d3ed99fc040c341f50f74e6b9cd017d8dc`. Accepted V0 package hash: `77ef233f9541072dbac0140d11dd84dac1a3494c60fb324b74413a71b25c0400`. Read-only revalidation remains 10/10 complete and exactly recovered. All 113 protected evidence/configuration/ledger files and 24 retained key files match their starting hashes; historical cost remains **3,163.653124 seconds**. See [preservation](../artifacts/v1_review/v0_preservation.json) and [V0 revalidation](../artifacts/v1_review/v0_strict_revalidation.json).

Measured stego package hash: `d70e5e3321e1e5003eaa7687ca867229892ada937d89a70660bb7e3665aed577`; its complete source is retained in [pilot_source](../artifacts/v1_review/pilot_source). Final package hash: `dd99e932b5b89b5def365cbb46f5dbe227abcb7d3f5cdb9e613a02c940cb47a3`. After stego execution, only evaluator evidence checks and ordinary-control prefix reporting changed in the package; sender, receiver, coders and neural backends did not. [Source manifest](../artifacts/v1_review/source_manifest.json) pins individual files; this is an uncommitted working-tree revision.

## Evaluator correction and CPU verification

Progress mode writes the current subset; final mode is read-only and reconciles expected case/work pairs, actual directories, existing result IDs, duplicates, unexpected/missing IDs, terminal failures, staged profiles, model/GPU identities and carrier hashes. It independently compares source/recovered bytes and the frozen source manifest. Authentication alone cannot establish equality.

A complete failed allocation is distinct from an incomplete allocation. Final default exit requires all recovered; `--allow-failures` requires complete coverage but permits documented failures. V0 keeps strict ten-case acceptance.

**41 CPU tests passed** (7.224 seconds in the packaged run). They cover partial/missing/duplicate/unexpected/mismatched case/work IDs, complete failing/passing allocations, terminal backend failure, profile tampering, byte/rank inversion, packet bounds, independent AES-GCM vectors, nonce lifecycle, strict UTF-8/prefix consistency, sorting/probability/sampling equivalence, gated synchronization, integer arithmetic boundaries and finite messages, independent fractional interval checks, pixel CDF/RGB posterior oracles, PNG preservation and synthetic saved-file sender/receiver integration. Synthetic adapters explicitly claim no GPU inference. [Test output](../artifacts/v1_review/cpu_tests.txt). Actual CPU CLI checks also returned 1 for the one-case partial allocation, 0 for strict V0, and 1 for strict V1: [CLI evidence](../artifacts/v1_review/cli_validation.json).

## Text optimization and reuse

RankCloak revision `ce853d42d6ba64065cb63c6bdfc0d825c62734cd` remains the source of the bounded byte/rank bridge, stable ordering, exact-byte model I/O, CUDA library loading, offload verification, reset and incremental replay precautions. V1 additionally adapts `revision_v3_entropy.py::{shannon_entropy_bits,entropy_eligible,generate_entropy_gated_span,recover_entropy_gated_span,calibrate_entropy_gate_thresholds}`; strict comparison and full eligible-distribution sampling replace upstream's inclusive/top-p assumptions. No sibling application imports or full research pipeline were added. [Attribution](../THIRD_PARTY.md).

Before optimization, the 616-token GPU replay under cProfile took 152.577 seconds, with 139.397 in filtering (91.4%). Cumulative categories included full-prefix detokenization 82.403, tokenization 39.784 and sorting 12.499 seconds; these categories overlap.

The optimization uses exact top-256 cutoff selection with explicit ties, unsorted float64 normalization, and model-local exact token-piece/prefix-byte caches. The inspected native detokenizer concatenates pieces for BOS-free carriers; its source hash and native tokenizer type are checked. Full-prefix tokenization is still performed for every candidate, including skips and completion. No precision, eligibility limit, sampling, prompt boundary, serialization or GPU replay rule changed.

On one immutable packet, the retained reference and optimized paths produced identical eligible IDs, raw probability bytes and ordering at all 616 matched states, identical sampling/carrier bytes, and identical recovered packets:

| Path | Encode | Decode |
| --- | ---: | ---: |
| Reference | 136.702 s | 136.725 s |
| Optimized | 43.035 s | 42.471 s |

This is 3.18×/3.22× on that diagnostic case, not a universal throughput claim. The two diagnostic carriers are not independent pilot observations. Longer arithmetic text streams still spend most time in required complete-prefix tokenization. [Equivalence evidence](../artifacts/v1_review/text_equivalence/result.json).

## Methods, environment and frozen pilot

All methods transport the same 292-byte AES-256-GCM packet: 8-byte header + 256-byte zero-padded slot, 12-byte nonce and 16-byte tag. Fresh run keys and unique random nonces are independent of sampling seeds. Each payload/context packet is encrypted once and reused unchanged by the three senders. Keys and packet bytes remain private.

Gating uses radix 16 and strict `H > threshold`; ordinary skipped positions update state but carry no bits. Two ordinary traces per modality froze these medians before stego outputs:

| Modality | Ordinary calibration positions | Threshold, bits |
| --- | ---: | ---: |
| Text | 2 × 1,024 | 0.5983972524635524 |
| Image | 2 × 2,976 channels | 3.2159513527579326 |

Float64 hexadecimal values, trace seeds/hashes and profiles are in [calibration](../artifacts/v1_review/profiles/v1_calibration.json). No failure-driven recalibration occurred.

The [Ziegler–Deng–Rush comparator](https://aclanthology.org/D19-1115/) was independently implemented, not copied from the unlicensed reference source at `14e982564aeaf9a33f7b4de440deda2184d17f12`. Approved A1 uses 32-bit half-open intervals, integer probability partitions, common-prefix emission, zero extension and observable stopping at 2,336 recovered bits. It validates/discards at most 31 zero suffix bits, with no EOF, endpoint dump or completion-time flush. It is an explicitly framed adaptation, not a bit-identical reference reproduction or new invention. [Comparator contract and limitations](../artifacts/v1_review/comparator.json).

GPU/model settings remain the V0 ones: RTX 5000 Ada, UUID `GPU-10d1f16f-9e79-08bb-b2ba-3353c04422cf`, physical device 1 mapped to logical CUDA 0, driver 590.48.01. Text uses Llama 3 8B Instruct Q4_K_M, model SHA-256 `86c8ea6c8b755687d0b723176fcd0b2411ef80533d23e2a5030f845d13ab2db7`, llama-cpp-python 0.3.23/CUDA runtime 12.4.127/cuBLAS 12.4.5.8. Image uses strict PixelCNN++ loading (5 residual blocks, 160 filters, 10 mixtures), checkpoint SHA-256 `a5ed558f6d4098ce3cbfd47658b7e3be37fae77b71a90c8a56f46a6266ff833f`, PyTorch 2.5.1+cu124.

Text explicitly requests `n_gpu_layers=-1`; initialization establishes 33/33 eligible layers offloaded. Batch/microbatch 1, all logits, approved graph/fusion/workspace/precision controls, full sequence reset and incremental evaluation remain. Image parameters/inputs/outputs are CUDA tensors, with evaluation/inference mode and deterministic float32 inference. All 32 V1 model processes have observed process-specific GPU activity and model allocation evidence. CPU/partial-offload fallback did not occur. [GPU jobs and commands](../artifacts/v1_review/gpu_jobs.json), [initialization evidence](../artifacts/v1_review/backend_initialization.json), [pinned environments](../artifacts/v1_review/reused_environment.json).

Fixtures were preselected I1 (gradient), I5 (noise), T1 (32 UTF-8 bytes) and T3 (64 bytes, non-ASCII), with the original forest prompt and shared 96-byte pixel row. They give four payload groups, one context/direction and twelve method units, not twelve independent payload groups.

## Twelve-case results

Status columns are packet complete / carrier complete / authenticated / exact source equality. Times exclude separately tabulated loading/setup. All twelve saved carriers are retained, including failures.

| Case | Source bytes | Delivered symbols | Packet bits recovered | P/C/A/E | Encode / decode s |
| --- | ---: | --- | ---: | --- | ---: |
| I1-fixed | 256 | 616 | 2336 | yes/yes/yes/yes | 45.5 / 45.2 |
| I1-gated | 256 | 650 | 2336 | yes/yes/yes/yes | 48.0 / 47.5 |
| I1-arithmetic | 256 | 2048 | 1450 | no/no/no/no | 411.6 / 406.6 |
| T1-fixed | 32 | 992 pixels / 2,976 channels | 2336 | yes/yes/yes/yes | 83.6 / 84.9 |
| T1-gated | 32 | 992 pixels / 2,976 channels | 2336 | yes/yes/yes/yes | 84.3 / 84.3 |
| T1-arithmetic | 32 | 992 pixels / 2,976 channels | 2336 | yes/yes/yes/yes | 84.4 / 84.2 |
| I5-fixed | 256 | 616 | 2336 | yes/yes/yes/yes | 50.6 / 50.8 |
| I5-gated | 256 | 640 | 2336 | yes/yes/yes/yes | 49.0 / 49.1 |
| I5-arithmetic | 256 | 2048 | 771 | no/no/no/no | 397.8 / 395.9 |
| T3-fixed | 64 | 992 pixels / 2,976 channels | 2336 | yes/yes/yes/yes | 84.1 / 84.4 |
| T3-gated | 64 | 992 pixels / 2,976 channels | 2336 | yes/yes/yes/yes | 84.3 / 84.4 |
| T3-arithmetic | 64 | 992 pixels / 2,976 channels | 2336 | yes/yes/yes/yes | 84.5 / 84.0 |

Fixed-rank and gated recovery passed in both directions; arithmetic passed on both PNG cases. Both failed text streams used all 2,048 tokens, with zero completion tokens and no authenticated output. Their receiver bit counts exactly matched their senders. Mean observed surprisal was 0.708683 and 0.376550 bits/token; mean quantization L1 was 7.28e-6 and 6.14e-6. Neither reached zero-extension lookahead. This supports low conditional information capacity as the main observed limitation, not a final-bit flushing failure.

A separate CPU test exposed A1's possible quantization stagnation: at width three, uniform-32 rounding/overflow removal can leave one bin straddling one half forever. A fractional oracle confirms it. The original random synthetic test wrongly required every such stream to succeed; it now separates deterministic success from explicit capacity failure. No coder, model fixture or threshold was altered to obtain success.

The evaluator reports `allocation_complete=true`, attempted=12, completed/authenticated/exact=10, `all_recovered=false`, failures=2. Each receiver was a different process launched after its sender exited, with exactly carrier/profile/context/key inputs and no sender diagnostics, packets, source, IDs, ranks or evaluator manifest. Pairing and input audits passed all twelve units. This is data-flow separation, not an adversarial OS sandbox. [Audit](../artifacts/v1_review/receiver_pairing_audit.json), [public final validation](../artifacts/v1_review/final_validation.json), [all viewable examples](../artifacts/v1_review/README.md).

Packet framing is 36 bytes; slot padding is 0/224/192 bytes for I1 and I5 / T1 / T3. Rank alignment padding is zero. Gated skips were 34/24 text tokens and 28/122 image channels. Arithmetic PNG stops were 530/570 channels, each with 31 discarded zero suffix bits. Suffix termination overlaps the last packet position; it is not added to delivered counts. Ordinary completion and arithmetic zero-bit positions are recorded separately. For arithmetic, packet_positions counts positive common-prefix emission positions; zero-bit steps are still packet-driven and included in packet_span. Thus packet_bearing summaries are not directly commensurate across methods; use packet_span/whole summaries for cross-method diagnostics. Surprisal and ranks refer to the normalized eligible distribution q, not unfiltered-model perplexity.

Results distinguish nominal useful rate from failure-inclusive exact goodput (zero for both failures), packet transport rate through packet stop, and serialized expansion. They retain separate bits/token, bits/channel and bits/pixel; an unfinished packet has undefined completion-based transport rate, not an invented successful rate.

Two predeclared ordinary controls were generated: a 2,048-token trace (seed 4301) with saved matched prefixes at 616/640/650/2,048, and one complete PNG (4302). They cost 371.909 and 87.796 seconds including setup. Their linked mean surprisal/log-rank diagnostics are descriptive only; shared prefixes/images are not independent control replicates. Scoring was collected inline, not through an uncounted model pass. [Control links](../artifacts/v1_review/control_links.json).

## Charged compute and projection

| V1 category | Charged seconds |
| --- | ---: |
| profiling | 168.482 |
| equivalence | 374.962 |
| calibration | 444.508 |
| pilot encoding | 1625.131 |
| pilot decoding | 1617.418 |
| controls | 459.705 |
| **V1 total** | **4690.205** |
| V1 initial allowance remaining | 2509.795 |
| V0 + V1 cumulative | 7853.858 |

All loading/imports/hash checks, occupied GPU time during CPU filtering, generation, replay, controls, failures and teardown are charged. CPU unit/aggregation checks do not load neural models. The V1 ledger is separate from unchanged V0; the overall 40-hour remainder is not additional authorization.

The first run's conservative midpoint forecast stopped at 7,535.736 seconds. The same future bounds with 25% reserve only on unspent work gave 6,881.937, under the unchanged 7,200-second hard cap. Only the wholly unstarted I5/T3 pairs continued in a fresh key/run namespace. Their never-encoded prior packet preparations are retained privately and explicitly superseded; no attempted fixture was retried. All twelve work IDs remain unique. A CPU calibration-launcher import error was fixed before any model launch. All model attempts, including capacity failures, remain in the ledger.

Mean measured cost per payload/method pair (two observations each):

| Direction/method | Generate s | Replay s | Cold loads s | Other setup/teardown s | Total charged s |
| --- | ---: | ---: | ---: | ---: | ---: |
| image-to-text/fixed | 48.0 | 48.0 | 5.3 | 26.2 | 127.6 |
| image-to-text/gated | 48.5 | 48.3 | 5.4 | 26.2 | 128.4 |
| image-to-text/arithmetic | 404.7 | 401.3 | 5.4 | 25.8 | 837.2 |
| text-to-image/fixed | 83.9 | 84.6 | 1.9 | 5.5 | 175.9 |
| text-to-image/gated | 84.3 | 84.4 | 1.9 | 5.6 | 176.2 |
| text-to-image/arithmetic | 84.4 | 84.1 | 1.8 | 5.6 | 176.0 |

The [projection](../artifacts/v1_review/compute_projection.json) uses each measured method separately:
`1.25 × (spent development + remaining development + 100C × sum_method,direction[generation + replay + setup + control] + required lossless replays)`.
Inline scores add zero **additional GPU passes**, not zero CPU work. Failures remain in means; reserve is applied once.

| Test contexts | Stego units | Ordinary-control policy | Projected whole-study cost, including development/reserve |
| --- | ---: | --- | ---: |
| 2 | 1200 | Separate by method (1200 jobs) | 181.63 h |
| 2 | 1200 | One trace per payload/context (400 jobs) | 160.58 h |
| 1 | 600 | Separate by method (600 jobs) | 98.85 h |
| 1 | 600 | One trace per payload/context (200 jobs) | 88.32 h |

Even the one-context **main stego generation/replay alone** projects to 45.04 hours before controls, development or reserve. These are conditional small-pilot estimates, not measured full-study costs or confidence bounds; the second context was not run. Sharing controls changes job costs/dependencies, not sample counts.

The remaining planned V1 qualification is estimated at 10.18 additional hours, or **12.73 with reserve**, versus 0.697 hours still authorized. This credits twelve pilot units against 152 development units, leaving 140, plus twelve calibration traces and up to 46 controls. The unmeasured static-mask arm uses measured sequence-check maximum cost as an explicit proxy, not a benchmark; control/calibration allocations are provisionally balanced by modality. Exact counts, assumptions and stage costs are exposed in the JSON. No larger work was launched from these estimates.

## Checkpoint and remaining work

Passed: evaluator correction, protocol-preserving text equivalence, CPU coder/pixel/packet checks, GPU execution, independent gated recovery in both modalities, arithmetic PNG recovery, complete pilot accounting and preservation of V0.

Not established: arithmetic image-to-text recovery on either selected case; full V1 qualification; 20-payload/two-context checks, the static-mask comparison, broader dataset provenance/preparation and development calibration, extended lossless checks, or a 40-hour-feasible study allocation. No held-out test generation, AUC/detector study, confidence intervals or manuscript claims were produced. No imperceptibility, broad robustness, statistical reliability or security-of-the-carrier claim follows from these examples.

The smallest next step is independent review of the retained arithmetic capacity failures and the cost projection before authorizing further GPU development or any protocol/budget amendment. Both directions and the comparator remain in scope. V2 must not start.

## Commands that actually ran

Exact model command vectors and return codes are in gpu_jobs.json. Key values are never logged. The controlling interpreter was `/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python`; text children used `.venv-generation-v3/bin/python`, image children `.venv/bin/python`.

    <control-python> -B scripts/calibrate_v1.py
    <control-python> -B -m imagecalgacus.v1_pilot --new-run runs/v1-pilot-001 --packet-run runs/v1-packets-001 --revision bc9e98d3ed99fc040c341f50f74e6b9cd017d8dc
    <control-python> -B scripts/finish_v1_pilot.py --first-run runs/v1-pilot-001 --new-run runs/v1-pilot-002 --new-packets runs/v1-packets-002
    <control-python> -B scripts/run_v1_controls.py
    <control-python> -B scripts/collect_v1_review.py --run runs/v1-pilot-001 runs/v1-pilot-002
    <control-python> -B scripts/audit_v1_evidence.py
    <control-python> -B scripts/project_v1_compute.py

The first pilot controller exited 3 at its forecast gate; continuation and final allocation validation exited 0 with recorded failures. Capacity sender/receiver jobs exited 2. Those statuses are not all-recovered claims. To revalidate public files without a model or key:

    <control-python> -B -m imagecalgacus.evaluate --run artifacts/v1_review/cases --references artifacts/v1_review/references.json --results artifacts/v1_review/results.jsonl --allow-failures

The default strict form, omitting --allow-failures, fails because two payloads did not recover. Private keys, packets, weights, environments and full diagnostic dumps are excluded from the review collection and Git.
