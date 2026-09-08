# V1.1 review checkpoint

Both saved arithmetic text failures are **capacity failures along low-information trajectories**. Fresh GPU receiver diagnostics reproduced 1,450 / 771 bits at 2,048 tokens. Every step narrowed the interval; neither stagnation nor finite-message termination occurred. No implementation bug was found or fixed. The separate A1 width-three stagnation limitation remains.

See [the self-contained results report](../../notes/v1_1_results.md), [compact arithmetic diagnostics](arithmetic_diagnosis.json), and [whole-project projection](compute_projection.json).

| Evidence | Result |
| --- | --- |
| [CPU tests](cpu_tests.txt) | 44 passed, including three focused diagnostic regressions |
| [Artifact revalidation](revalidation.json) | V0 unchanged 10/10; V1 retains 10 exact + 2 failures |
| [Preservation](preservation.json) | 700 protected files / 51 key copies unchanged; original ledger prefix intact |
| [GPU jobs and exact command vectors](gpu_jobs.json) | Two fresh text receivers; 33/33 eligible layers offloaded and observed execution |
| [Budget](budget.json) | 834.582 new seconds; 1,675.213 seconds remain in the original V1 allowance |
| [Source identities](source_manifest.json) | Only receiver diagnostic output changed within the application package |
| [Pre-execution diagnostic scope/bounds](diagnostic_plan.json) | Two saved-carrier replays, no new observations or encoding |

The new aggregate receiver reports are [I1](diagnostics/I1/receiver.json) and [I5](diagnostics/I5/receiver.json). Inspect the original [I1 carrier](../v1_review/cases/I1-arithmetic/carrier.txt) and [I5 carrier](../v1_review/cases/I5-arithmetic/carrier.txt) in the accepted V1 packet. Those carriers, original reports, manifests and results were not rewritten or superseded. The diagnosis adds **zero** independent pilot observations.

The authorized prospective amendment in [the methodological plan](../../plan/crossmodal_steganography_focused_research_plan.md) and [implementation plan](../../plan/implementation_plan.md) specifies 20 held-out payloads/direction, one existing context/direction and all methods: **120 stego units**, with up to **40 independent ordinary traces** shared within payload groups. No held-out carrier was generated. Estimated remaining qualification is **10.181 hours unreserved / 12.727 reserved**; whole-project estimate including history, qualification, main work, lossless checks and one reserve is **30.806 / 40 GPU-hours**. Neither forecast grants additional phase authority.

V1 is **not fully qualified**. Required static-mask/two-context development, remaining methods/calibration/control checks, corpus manifests and final compute/protocol freeze are still outstanding; the notes enumerate exact counts. No successful complete arithmetic text packet is established, and no arbitrary rerolled success is required to recognize a capacity failure.

Private interval traces (bounds, emitted bits, probability arrays) remain under ignored `.runtime/v1_1/`, mode 0600. Keys, original encrypted packets, weights and environments are excluded. Receiver inputs were exactly carrier/profile/context/key; original packets were read only by the separate CPU audit after receiver exit. This public review packet is **not** a receiver input directory.

CPU reproduction of the compact diagnosis requires the retained private traces/packets locally; independent reviewers without them can inspect the public checkpoints, tests, code, saved artifacts and original reports. Projection regeneration needs the existing V1 ledger/control records. Use new output paths; reporting commands reject overwrites. No V2, commit, push or publication occurred.
