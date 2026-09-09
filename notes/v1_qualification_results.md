# V1 qualification results

## Decision

**V1 is qualified for the bounded prospective study.** Every frozen qualification work item is accounted for, mandatory fixed-rank recovery checks pass, and the measured whole-project forecast remains below 40 GPU-hours. This is a development qualification decision, not authorization to execute V2 or a claim of broad reliability, security, imperceptibility or statistical power.

**Complete arithmetic image-to-text recovery remains unobserved (0/8).** These are retained capacity outcomes under the unchanged 2,048-token cap, not excluded observations. Arithmetic PNG recovery is 8/8. Two successful new arithmetic PNG cases exhibit transient finite-precision non-narrowing, described below.

Machine-readable [acceptance](../artifacts/v1_qualification_review/acceptance.json), [coverage](../artifacts/v1_qualification_review/coverage.json), and the [review index](../artifacts/v1_qualification_review/README.md) are the primary evidence. No qualification condition remains pending.

## Starting point and preservation

Accepted revision: b5f2d1e3b9e901e5dfe6a181b6ca5d95dc35ac4b. The initial tree was clean. Source/context selection and the qualification allocation were unchanged.

| Allocation | Accepted credits | Newly executed | Final evidence |
|---|---:|---:|---|
| Fixed sequence-arm text | 4 | 36 | 40/40 exact |
| Fixed static-arm text | 2 | 38 | 40 accounted: 22 exact, 18 drift failures |
| Fixed PNG | 4 | 36 | 40/40 exact |
| Gated/arithmetic timing | 8 | 24 | 32 accounted: 24 exact, 8 text capacity failures |
| Ordinary development traces | 4 | 12 | 16 complete |
| Independent allocated controls | 2 | 46 | 48 complete |
| Lossless PNG receiver checks | 0 | 20 | 20/20 exact |

There are 152 stego units across 80 payload/context groups, but only **40 distinct payloads: 20 per direction**, each used under two contexts. Methods, arms and repeated contexts are not independent payload observations. Diagnostic checks and lossless replays add no stego observations.

All 1,013 protected historical files are unchanged. The audit also verifies the original V1 ledger prefix and unchanged V0 usage. Accepted public evidence revalidated without regeneration: V0 10 exact; V1 10 exact plus two capacity failures; V1.2 five exact plus one static-drift failure. Original keys, packets and logs remain private. See [preservation](../artifacts/v1_qualification_review/preservation.json) and [accepted revalidation](../artifacts/v1_qualification_review/accepted_revalidation.json).

## Continuation implementation and boundaries

Changes are concentrated in stage-specific accounting, the existing pilot entry point, a small qualification continuation helper, the existing projection script, focused tests and a CPU-only finalizer. Packet, rank, entropy, arithmetic, text/image backend and vendored probability calculations remain byte-for-byte unchanged.

The idempotent amendment sets an absolute V1 limit of 50,400 seconds. V0 remains 7,200 seconds; neither ledger was reset. Reapplying the authorization does not add another 43,200 seconds; conflicting amendments are rejected. The overall limit remains 144,000 seconds.

Continuation selects pending frozen IDs. Immutable atomic terminal records are authoritative, with append-only events and recovery of an interrupted terminal/event append. Valid retained carriers resume at a fresh receiver; incomplete senders stop for inspection, not rerolling. Interrupted-process accounting uses conservative bounds and rejects live jobs. These paths are CPU-tested; this execution needed no infrastructure recovery or retry.

Before inference, all eight started packet groups were authenticated against their sources. I5 and T3 use the original **second** pilot packet run, not the unused first run. I1/I5/I6 and T1/T3/T6 retain their original packet/key bindings. The other 72 groups received one new sealed packet each, retained for every allocated method/arm. Final evaluation rechecks each packet digest against its binding and source. No legacy group was re-encrypted.

Receivers receive only carrier/profile/context/key in four-file inboxes. Every receiver launched after sender exit in a distinct process. Sources, packets, token IDs, ranks and evaluator records were not receiver inputs. Optional bit/interval diagnostics are output-only private files under ignored .runtime; the evaluator inspects them after receiver exit, without an extra model pass.

Receiver reports have no native source-hash field. New provenance uses frozen controller/group checks, the recorded sender hash and fresh receiver command/PID/model evidence. Historical identities are retained, not attributed to the new controller. The reporting-only finalizer records its hash separately.

## Execution and GPU evidence

The queue was frozen before outcomes: I7/prompt1 sequence/static pair first, allocated second-context traces/timing early, remaining numeric groups and associated controls, then the preselected lossless checks. The first pair recovered exactly in **177.336 charged seconds**, within its 300-second bound. Execution continued through the whole queue with group-level coverage/forecast checks and 20 retained internal checkpoint snapshots.

All 346 new model jobs ran serially on NVIDIA RTX 5000 Ada Generation, UUID GPU-10d1f16f-9e79-08bb-b2ba-3353c04422cf, PCI 00000000:09:00.0, physical device 1 mapped to logical device 0. Every job has positive process-specific SM activity.

- Text: pinned Llama 3 8B Instruct Q4_K_M, SHA-256 86c8ea6c8b755687d0b723176fcd0b2411ef80533d23e2a5030f845d13ab2db7. Existing CUDA llama-cpp-python 0.3.23 environment; explicit n_gpu_layers=-1; verified **33/33** eligible-layer offload; logits_all=True; batch/ubatch 1; context 4,096. RankCloak-derived library loading, graph/fusion/workspace/numerical controls, full sequence reset and incremental replay remain unchanged.
- Image: pretrained CIFAR-10 PixelCNN++, SHA-256 a5ed558f6d4098ce3cbfd47658b7e3be37fae77b71a90c8a56f46a6266ff833f; 160 filters, 5 residual blocks, 10 mixtures. PyTorch 2.5.1+cu124; strict checkpoint loading; CUDA parameters/inputs/outputs; evaluation/inference modes; deterministic controls; TF32 disabled.
- No installation, model change, new GPU, CPU inference fallback or partial offload. Attribution remains in [THIRD_PARTY.md](../THIRD_PARTY.md), including RankCloak revision ce853d42d6ba64065cb63c6bdfc0d825c62734cd and the separately attributed A1 adaptation.

[GPU jobs](../artifacts/v1_qualification_review/gpu_jobs.json) records commands, costs, activity and local log references; [initialization evidence](../artifacts/v1_qualification_review/backend_initialization.json) retains offload/buffer lines and log hashes.

## Outcomes and limitations

Coverage is allocation-complete: attempted 152, completed/authenticated/exact 126, recorded failures 26; no missing, duplicate, unexpected, unfinished or invalid-evidence IDs. Sender packet completion is 144. All 152 carriers are retained. **all_recovered=false is correct**: 18 static replay failures and eight arithmetic capacity failures are legitimate outcomes.

[Static pairs](../artifacts/v1_qualification_review/static_pairs.json) preserve the same packet within each pair. Sequence recovery is 20/20 for each prompt. Static recovery is 8/20 for prompt1 and 14/20 for prompt2; all 18 failures retain literal UTF-8 and tokenization-drift/replay evidence. No carrier was repaired or normalized. Sender completion, receiver completion/conformance, authentication and equality remain separate fields.

Gated rank coding recovered 8/8 text and 8/8 PNG payloads. Arithmetic recovered 8/8 PNG payloads. Arithmetic text recovered these prefixes out of 2,336 bits:

| Payload | Prompt1 | Prompt2 |
|---|---:|---:|
| I1 | 1,450 (historical) | 2,104 |
| I5 | 771 (historical) | 789 |
| I6 | 1,604 | 2,048 |
| I7 | 1,294 | 825 |

The original two observations and [V1.1 diagnosis](v1_1_results.md) are unchanged. For all six new text failures, recovered prefixes equal the private packet prefix; source-window selection and independent Fraction/interval and scalar-partition checks pass. Eligible surprisal is approximately 791.4–2,105.0 bits. No interval stopped narrowing, no single-bin collapse occurred, and zero-extension/termination was not reached. The longest new text zero-bit run was 468 positions while intervals continued to narrow. Evidence supports low information rate under the fixed cap, not synchronization or termination defects.

A1's separate finite-precision limitation remains. Among six newly instrumented arithmetic PNG cases, **T3/row2** had two consecutive unchanged steps at width 2; **T7/row2** had seven unchanged steps, longest run six, at widths 2 and 25. Each reduced 256 eligible values to one quantized bin, then resumed progress and recovered exactly. These transient partition-collapse effects do not fix the known stationary synthetic stagnation case. All independent checks passed. The six new PNG cases reached termination with 24, 27 or 30 discarded zero-extension suffix bits.

[Arithmetic audits](../artifacts/v1_qualification_review/arithmetic_audits.json) publish compact summaries, not packet bits or interval endpoints. No coder correction, precision/cap/threshold change, reroll or additional arithmetic replay was used. Raw historical labels remain unchanged; reconciled results add adjudicated outcome classes.

## Ordinary, control and lossless evidence

The 12 new ordinary traces audit, not recalibrate, the frozen thresholds. Strict H > threshold remains: text 0.5983972524635524; image 3.2159513527579326. Traces contain 1,024 text positions or 2,976 image channel values. Context2 distributions differ from context1; [threshold audits](../artifacts/v1_qualification_review/threshold_audit.json) report this without selecting new thresholds.

All 48 independent allocated controls are complete, 12 per modality/context cell. Text controls retain 2,048-token streams and matched prefixes; PNG controls retain full canvases. Available likelihood/rank diagnostics were collected inline, without additional model passes. Shared prefixes are links, not independent method-specific replicates. Original pilot cross-payload associations remain intact.

One historical exception is explicit: control-text-4301 did not retain the later-required 614-token prefix for I1/prompt1/static. That comparison has no matched-prefix score; its original full control remains counted once. No score was invented or accepted control regenerated. All new allocated prefixes are present. I13–I20 and T13–T20 groups are outside the frozen development control allocation, not execution shortfalls. See [control coverage](../artifacts/v1_qualification_review/control_coverage.json) and [shared links](../artifacts/v1_qualification_review/control_links.json).

The 20 pre-frozen lossless selections are T1–T10 under both rows, fixed method. Original PNGs were preserved; copies used compression level 9 and no ancillary metadata. CPU checks established identical RGB mode, 32×31 dimensions and pixel bytes. All fresh receivers authenticated and independently matched source text. Final CPU reconciliation rechecked current file/pixel hashes, source equality, unchanged reports and input boundaries. These are preservation replays, not new stego observations.

All **96** retained development text carriers, including failures, passed strict UTF-8 raw save/load byte equality. This does not erase static tokenization drift.

## Measured timing and budget

Mean charged sender/receiver seconds include imports, hashing, loading, occupied CPU filtering, inference, serialization and teardown. Failed-attempt costs are included.

| Direction / method | Context1 sender / receiver | Context2 sender / receiver | Cases per context |
|---|---:|---:|---:|
| Image→text fixed sequence | 63.413 / 63.173 | 55.374 / 55.404 | 20 |
| Image→text fixed static | 30.828 / 25.375 | 30.765 / 27.608 | 20 |
| Image→text gated | 75.875 / 74.975 | 60.436 / 60.283 | 4 |
| Image→text arithmetic | 395.808 / 390.193 | 352.364 / 351.447 | 4 |
| Text→PNG fixed | 88.498 / 88.345 | 88.291 / 88.367 | 20 |
| Text→PNG gated | 88.217 / 87.957 | 88.042 / 88.391 | 4 |
| Text→PNG arithmetic | 88.500 / 88.468 | 88.849 / 88.657 | 4 |

Static means include early failures; they are descriptive, not an assumption that future receivers fail early. Text control means are 403.561/349.357 seconds for prompts1/2; PNG controls 88.351/88.501 for rows1/2. [Timing summaries](../artifacts/v1_qualification_review/method_context_summary.json) include ranges and internal generation/replay/load/other-process separation.

This task: 134 senders **10,116.555s**, 134 receivers **9,923.038s**, 58 traces **11,961.197s**, 20 lossless receivers **1,769.393s**; total **33,770.183s (9.3806h)**. Nonzero exits are retained: six arithmetic sender capacity exits, six receiver capacity exits and 17 new static replay failures. No infrastructure errors or retries occurred.

| Accounting / forecast term | Seconds |
|---|---:|
| Historical V0 | 3,163.653 |
| V1 before this task | 6,225.327 |
| This continuation | 33,770.183 |
| Cumulative actual V0 + V1 | **43,159.162** |
| V1 actual / absolute limit | **39,995.509 / 50,400** |
| Remaining V1 allowance | **10,404.491** |
| Remaining qualification | **0** |
| Prospective main generation | 14,822.455 |
| Prospective main receiver replay | 14,676.928 |
| Main stego cold loading | 436.339 |
| Main stego other occupied time | 1,932.741 |
| Main shared controls, inclusive | 9,838.228 |
| Whole-project subtotal | 84,865.854 |
| One 25% reserve | 21,216.463 |
| Whole-project forecast | **106,082.317s = 29.4673h** |

Forecast = actual history + 20 units per direction/method under prompt1/row1 + 20 independent controls per direction. Each future stego unit includes fresh sender/receiver costs from its method/context cell, including failed arithmetic observations. The four main stego cost rows sum to 31,868.463s and are not counted twice. Completed lossless checks moved into history: **no extra 20-job main-study term**. Inline scoring adds no model pass.

One reserve applies to the whole subtotal, including history (conservative). Phase headroom checks use the same reserve, not another expense. The authorization extension is permission, not cost. The final estimate is close to the initial 29.6994h and below 40h, conditional on the pinned machine/profile and observed trajectories. Only four cases per context support gated/arithmetic means; held-out outcomes and host variation remain uncertain. No held-out carrier was generated to improve this estimate. See [projection](../artifacts/v1_qualification_review/compute_projection.json).

## Verification and protocol freeze

The final CPU suite passed **62 tests**, including existing independent arithmetic finite-message/partition vectors and static/sequence serialization checks, eight continuation/budget tests and two namespace/public-coverage tests. Source-preparation tests use the retained local cache. Public-only verification separately reproduced complete 152-unit coverage and 126 exact source equalities; it does not repeat key-dependent GPU inference.

Commands actually run successfully:

~~~sh
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m unittest discover -s tests -v
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.v1_pilot --complete-qualification runs/v1-qualification-complete
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/finalize_v1_qualification.py --run runs/v1-qualification-complete
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/finalize_v1_qualification.py --verify-public artifacts/v1_qualification_review
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.runtime --stage v1 --status
~~~

The continuation command is finished, not a request for another run. Individual sender/receiver commands are in GPU evidence. Private finalization needs original keys/packets/logs; public verification needs none of them and follows prior review references.

Execution package hash: 12e3ed9fee516be823261afd53cada8173530db58f163ee0868d3bd84937512d. Manifest SHA-256: 9c20a5c11896c84d0f7accf2c5e4ad99c4e432f7bdd02bdaa2056ae3b048346f. Allocation SHA-256: 60e129121f585ad431d2fee10351a24d5e419a10bfc171c813afb33b0cb41569. Full file identities are in the [execution freeze](../artifacts/v1_qualification_review/execution_freeze.json). The reporting-only finalizer was added later and has a separate hash; no historical job is claimed to have run it.

The [protocol/compute freeze](../artifacts/v1_qualification_review/protocol_compute_freeze.json) preserves the 292-byte authenticated packet, radix16/gated/A1, main complete-prefix eligibility, shared private pixel row, thresholds, text cap/tail and 32×31 delivered RGB PNG contract. Bits/token, bits/channel value and bits/pixel remain distinct; offered payload rates are not recovered goodput for failures. The prospective allocation remains 20 held-out payloads/direction, prompt1/row1, 120 stego units and up to 40 shared controls.

Pre-execution inspection/writer mistakes and a reporting-only missing-field assumption were corrected on CPU without affecting model behavior or regenerating evidence. Final review scans exclude retained key/packet bytes, weights, environments and private traces.

**Next step:** independent review of this qualification decision and freeze. The bounded prospective study requires separate authorization. No V2 work, commit, push or publication was performed.
