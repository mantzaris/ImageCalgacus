# V1 review packet

Complete 12-unit development allocation: **10 exact recoveries, 2 arithmetic text capacity failures**. V1 is not fully qualified; V2 has not started. Read [the results report](../../notes/v1_results.md).

| Case | Source | Delivered artifact | Recovered output |
| --- | --- | --- | --- |
| I1-fixed | [source](cases/I1-fixed/source.png) | [carrier](cases/I1-fixed/carrier.txt) | [recovered](cases/I1-fixed/recovered.png) |
| I1-gated | [source](cases/I1-gated/source.png) | [carrier](cases/I1-gated/carrier.txt) | [recovered](cases/I1-gated/recovered.png) |
| I1-arithmetic | [source](cases/I1-arithmetic/source.png) | [carrier](cases/I1-arithmetic/carrier.txt) | none — capacity failure |
| T1-fixed | [source](cases/T1-fixed/source.txt) | [carrier](cases/T1-fixed/carrier.png) | [recovered](cases/T1-fixed/recovered.txt) |
| T1-gated | [source](cases/T1-gated/source.txt) | [carrier](cases/T1-gated/carrier.png) | [recovered](cases/T1-gated/recovered.txt) |
| T1-arithmetic | [source](cases/T1-arithmetic/source.txt) | [carrier](cases/T1-arithmetic/carrier.png) | [recovered](cases/T1-arithmetic/recovered.txt) |
| I5-fixed | [source](cases/I5-fixed/source.png) | [carrier](cases/I5-fixed/carrier.txt) | [recovered](cases/I5-fixed/recovered.png) |
| I5-gated | [source](cases/I5-gated/source.png) | [carrier](cases/I5-gated/carrier.txt) | [recovered](cases/I5-gated/recovered.png) |
| I5-arithmetic | [source](cases/I5-arithmetic/source.png) | [carrier](cases/I5-arithmetic/carrier.txt) | none — capacity failure |
| T3-fixed | [source](cases/T3-fixed/source.txt) | [carrier](cases/T3-fixed/carrier.png) | [recovered](cases/T3-fixed/recovered.txt) |
| T3-gated | [source](cases/T3-gated/source.txt) | [carrier](cases/T3-gated/carrier.png) | [recovered](cases/T3-gated/recovered.txt) |
| T3-arithmetic | [source](cases/T3-arithmetic/source.txt) | [carrier](cases/T3-arithmetic/carrier.png) | [recovered](cases/T3-arithmetic/recovered.txt) |

Image-to-text cases also retain recovered.gray (256 raw source pixels) when recovery succeeded. All PNG carriers are 32 × 31 RGB8. T1/T3 contain 32/64 original UTF-8 bytes; T3 is non-ASCII. Failed text artifacts contain the full 2,048-token budget and were not rerolled.

Important evidence:

- [Frozen allocation](pilot_manifest.json), [fresh-run continuation lineage](continuation_manifest.json), [portable references](references.json), [profiles/calibration](profiles/v1_calibration.json).
- [Results JSONL](results.jsonl), [coverage](coverage.json), [final validation](final_validation.json), [receiver/pairing audit](receiver_pairing_audit.json).
- [GPU jobs, execution and sampled memory](gpu_jobs.json), [budget](budget.json), [measured projection](compute_projection.json).
- [CPU tests](cpu_tests.txt), [text equivalence](text_equivalence/result.json), [arithmetic framing](comparator.json), [shared controls](control_links.json).
- [Preserved V0](v0_preservation.json), [source identities](source_manifest.json), [exact measured stego source](pilot_source), [attribution](THIRD_PARTY.md).

From the repository root, using the existing control interpreter, this CPU-only command reports complete coverage while retaining failures:

    <control-python> -B -m imagecalgacus.evaluate --run artifacts/v1_review/cases --references artifacts/v1_review/references.json --results artifacts/v1_review/results.jsonl --allow-failures

Omitting --allow-failures returns a failing strict acceptance status. A zero exit with that flag is not proof of all-recovered.

Public case directories contain ground truth and MUST NOT be receiver input directories. Decoding requires a fresh process and a separate directory holding only carrier, frozen profile, shared context and the locally retained key, plus declared model/runtime assets. Keys, original encrypted packets, weights, private environments and full traces are intentionally absent here.

There are four independent payload groups, not twelve, and only two shared ordinary controls. Source snapshots are for inspection, not a new model installation or independent set of runs. The two unused initial packet preparations for I5/T3 never produced artifacts and are explicitly superseded by the fresh continuation key namespace.
