# V1 qualification review

**V1 qualified; V2 not executed or authorized.** The frozen development allocation is complete. See [acceptance](acceptance.json), [coverage](coverage.json) and the self-contained [results report](../../notes/v1_qualification_results.md).

| Required evidence | Result |
|---|---|
| Fixed-rank sequence text | 40/40 exact |
| Fixed-rank PNG | 40/40 exact |
| Static comparison | 40 accounted: 22 exact, 18 tokenization-drift failures |
| Gated/arithmetic timing | 32 accounted: 24 exact, 8 arithmetic text capacity failures |
| Ordinary traces / independent controls | 16 / 48 complete |
| Lossless PNG fresh-receiver checks | 20/20 exact |
| Raw UTF-8 byte save/load checks | 96/96 equal |
| CPU suite | 62 tests pass |
| Historical preservation | 1,013 files and original ledger history unchanged |

Overall: 152 attempted, 126 exact, 26 recorded failures; no missing, duplicate or unfinished work. The false all_recovered field is intentional. Forty distinct payloads, two contexts each, produce 80 correlated payload/context groups—not 80 independent payloads.

## Inspect the evidence

- [Results JSONL](results.jsonl), [failures](failures.json), [paired static/sequence outcomes](static_pairs.json), [method/context timings](method_context_summary.json).
- [Arithmetic audits](arithmetic_audits.json): original two text failures reference accepted V1.1. All eight arithmetic text attempts remain capacity failures; complete packet recovery was not observed. Six new text audits show correct recovered prefixes and narrowing intervals, not stagnation or termination failure. Two successful new PNG arithmetic cases show transient single-bin/non-narrowing steps; the separate A1 finite-precision limitation remains.
- [Ordinary/control provenance](ordinary_and_controls.json), [shared links](control_links.json), [control coverage](control_coverage.json), [threshold audit](threshold_audit.json). Thresholds were not recalibrated. One old control lacks the later I1/prompt1/static 614-token prefix score; it remains explicitly unavailable. All new allocated prefixes are present. Shared traces/prefixes are not extra control replicates.
- [Lossless PNG evidence](lossless_png.json) and [UTF-8 checks](utf8_lossless.json). T1–T10, both rows, were selected before outcomes; these are preservation checks, not new stego units.
- [GPU jobs](gpu_jobs.json), [backend initialization](backend_initialization.json), [receiver/packet boundaries](receiver_and_packet_checks.json). All 346 new jobs have observed GPU activity; text reports verify 33/33 full offload and image reports verify strict CUDA inference.
- [Execution freeze](execution_freeze.json), [completion events](qualification_events.jsonl), [work provenance](work_records.json), [final checkpoint](latest_internal_checkpoint.json), [protocol/compute freeze](protocol_compute_freeze.json).
- [Tests](cpu_tests.txt), [public-only revalidation](public_verification.json), [accepted revalidation](accepted_revalidation.json), [preservation audit](preservation.json).

Raw case evaluations are retained; results JSONL adds adjudicated failure labels without rewriting original reports. Source equality belongs to the evaluator. No receiver consumed sources, packets, saved IDs/ranks, diagnostic traces or evaluator records. Receiver reports do not contain native source hashes; provenance explicitly identifies the frozen group/controller evidence instead of inventing that field.

New viewable examples:

- I7/prompt1: [source PNG](cases/I7-prompt1-fixed-sequence/source.png), [sequence text](cases/I7-prompt1-fixed-sequence/carrier.txt), [recovered PNG](cases/I7-prompt1-fixed-sequence/recovered.png), [paired static text](cases/I7-prompt1-fixed-static/carrier.txt).
- Retained static drift: [I1/prompt1 carrier](cases/I1-prompt1-fixed-static/carrier.txt) and [receiver failure](cases/I1-prompt1-fixed-static/receiver.json).
- Non-ASCII source under row2: [T3 source](cases/T3-row2-fixed/source.txt), [PNG carrier](cases/T3-row2-fixed/carrier.png), [recovered text](cases/T3-row2-fixed/recovered.txt).
- Successful arithmetic PNG with transient finite-precision effects: [T7/row2 carrier](cases/T7-row2-arithmetic/carrier.png), [recovery](cases/T7-row2-arithmetic/recovered.txt).

The other new carriers and available recoveries are under cases/. Historical case paths reference [V0](../v0_review/), [V1](../v1_review/), [V1.1](../v1_1_review/) and [V1.2](../v1_2_review/) instead of copying those packets wholesale.

## Budget and freeze

This task used **33,770.183 charged seconds**. Total V1 usage is **39,995.509 / 50,400 seconds**, leaving **10,404.491 seconds**; V0 remains 3,163.653 seconds. No GPU jobs remain active. [Budget](budget.json) retains history and the [idempotent V1-only authorization](v1_gpu_authorization.json).

The [whole-project forecast](compute_projection.json) is **29.4673 hours**, including actual history, the prospective 120-unit main study, 40 shared controls and one 25% reserve. Remaining qualification is zero. The 20 completed lossless jobs are in history, not charged again prospectively. The 12-hour authorization extension itself is not a forecast expense. Small method/context samples and future trajectories remain sources of uncertainty.

No model, packet, coder, probability rule, eligibility rule, context, cap or threshold changed. The main study remains prompt1/row1 and complete-prefix text eligibility. Execution package hash: 12e3ed9fee516be823261afd53cada8173530db58f163ee0868d3bd84937512d; accepted base revision b5f2d1e. The CPU finalizer has a separately recorded reporting hash and is not retroactively attributed to historical model jobs.

## Recheck without model inference

From the repository root, using the retained compatible CPU interpreter:

~~~sh
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/finalize_v1_qualification.py --verify-public artifacts/v1_qualification_review
~~~

This successfully rechecks public source equality and complete coverage; it is not a claim to rerun GPU decoding without retained keys. Private finalization and original execution commands are documented in the results report. Do not start another run to inspect this packet.

Keys, encrypted packets, weights, private environments and detailed interval/bit traces are excluded. Public commands may reference retained local private paths but contain no key or packet bytes. No commit, push, V2 carrier generation or publication occurred. The next step is independent review of this qualification/freeze; V2 needs separate authorization.
