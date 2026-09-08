# V1.2 review checkpoint

**Six development units ran: five exact recoveries and one retained static
tokenization-drift failure.** Source/context preparation and the comparison arm
are ready; V1 is **not fully qualified**. No held-out carrier, extra control,
calibration, arithmetic rerun or V2 job was generated.

Start with [the results note](../../notes/v1_2_results.md),
[batch coverage](batch_coverage.json), [compact results](results.jsonl) and
[the cost projection](compute_projection.json). Accepted evidence is referenced,
not copied: [V0](../v0_review/README.md), [V1](../v1_review/README.md),
[V1.1 diagnosis](../v1_1_review/README.md).

## Frozen preparation and allocation

- [80 source payloads and preparation rules](../../data/qualification_v1/README.md);
  [source manifest](../../data/qualification_v1/manifest.json), SHA-256
  `9c20a5c11896c84d0f7accf2c5e4ad99c4e432f7bdd02bdaa2056ae3b048346f`.
  Includes 20 development and 20 held-out payloads per direction, with original
  indices/byte offsets, hashes and terms. Held-out files are source payloads only.
- [Source download lock](../../configs/v1_sources.json), four frozen
  [contexts](../../data/qualification_v1/contexts/), and unchanged original fixtures.
- [Full qualification allocation](../../configs/v1_qualification.json):
  152 stego units, 16 ordinary traces, up to 48 controls. Initial accepted credits
  12/4/2 give 140/12/46 pending. [Credit events](qualification_events.jsonl)
  add these six outcomes; [current coverage](qualification_coverage.json)
  leaves **134 stego, 12 ordinary and up to 46 controls pending**.
- [Pre-generation batch freeze](batch_manifest.json) and
  [source/configuration preflight identities](preflight_freeze.json).
  The immutable allocation retains its initial pending states; events/current
  coverage supply execution status rather than rewriting history.

Reproduction commands and selection/exclusion details are in the source README
and results note. Both source preparations yielded identical generated files.
I6 was Fashion-MNIST train index 1/class 0. T6 was ebook 11 bytes [1570,1632):
62 unchanged UTF-8 bytes. Prompt1/row1 are unchanged; prompt2 is the exact soup
prompt; row2 is independent PCG64(2002) RGB bytes. No outcome-based selection or
cryptographic seed derivation occurred.

## Comparison and inspectable artifacts

The [static profile](static_profile.json) is a fixed-rank **development-only**
opt-in. RankCloak's singleton `T(D([v]))=[v]` criterion replaces only the
complete-prefix check; top-256-before-filtering, exclusions, float64 PMFs,
ID ties, prompt boundaries and ordinary completion are shared. The default
sequence profile remains unchanged. Actual static UTF-8 is saved even with
tokenization drift, never repaired or decoded using sender IDs.

| Unit / artifact directory | Delivered carrier | Independent result | Charged pair s |
| --- | --- | --- | ---: |
| [I6, prompt1, sequence](cases/I6-prompt1-fixed-sequence/) | 616 tokens, 2,177 B | Exact | 113.795 |
| [I6, prompt1, static](cases/I6-prompt1-fixed-static/) | 613 reconstructed tokens, 2,708 B | Drift failure | 52.849 |
| [I6, prompt2, sequence](cases/I6-prompt2-fixed-sequence/) | 616 tokens, 2,797 B | Exact | 117.087 |
| [I6, prompt2, static](cases/I6-prompt2-fixed-static/) | 616 tokens, 2,925 B | Exact | 61.012 |
| [T6, row1, fixed](cases/T6-row1-fixed/) | RGB PNG, 2,220 B | Exact | 178.105 |
| [T6, row2, fixed](cases/T6-row2-fixed/) | RGB PNG, 2,475 B | Exact | 177.692 |

Each directory retains source, actual carrier, available recovered outputs
(including viewable recovered image PNGs), sender/receiver reports and independent
evaluation. PNGs are 32×31 RGB: 992 pixels, 2,976 channel values, not 2,976 pixels.
All six senders completed the 292-byte packet; five receivers authenticated,
completed and exactly recovered. The failed static file drifted from 616 sender
tokens to 613 reconstructed tokens. Receiver failure at zero-based position 247
matches the first sender-side mismatch; only 988 packet bits were recovered.
There is deliberately no recovered payload for that case.

Each text arm pair transported the same sealed packet. Receiver inputs were
only carrier/profile/context/key, in fresh processes after sender exit.
No packet, reference, digest, rank/token trace or sender cache was an input.
The public review directories are **not** receiver inboxes: they also contain
evaluator evidence. Actual restricted four-file inbox commands are recorded
in [GPU jobs](gpu_jobs.json); retained keys remain private.

## Verification, budget and limits

[Final CPU suite](cpu_tests_final.txt): **52 passed**.
[V0 strict revalidation](v0_revalidation_correct_phase.json): **10/10**.
[V1 revalidation](v1_revalidation.json): complete allocation, ten exact and two
unchanged capacity failures. [Public artifact validation](public_artifact_validation.json)
rechecks these six saved copies. [Focused audit](focused_final_audit.json)
independently checks cost sums, nonce uniqueness/pairing, process identities,
timeouts, secret exclusion and pending counts.

All twelve jobs used the selected RTX 5000 Ada UUID ending `c04422cf`.
Text retained verified **33/33 full offload** and GPU reset/numerical controls;
PixelCNN++ retained strict CUDA parameter/input placement and inference.
See [initialization evidence](backend_initialization.json) and [per-job activity](gpu_jobs.json).
No dependency, weight, model or runtime was changed.
[Source identities](source_manifest.json) distinguish the frozen inference
package from later CPU-only reporting/test documentation changes.

New charged time: **700.539619 s**; V1 total **6,225.326668 / 7,200 s**;
remaining **974.673332 s**. All loading, CPU processing during occupancy, failures,
serialization and teardown are included. [Budget](budget.json).
All **725 protected files** and the historical ledger prefix are unchanged:
[preservation](preservation.json).

Remaining qualification is projected at **9.118 h unreserved**
(**11.398 h with standalone 25% headroom**). Whole-project forecast:
**29.694 h with one reserve**, including history, remaining qualification,
120 main stego units, up to 40 shared controls and 20 additional lossless
PNG replays. It does not add the standalone development reserve again.
Each new context/static cell has only one measurement; other second-context
methods/controls remain explicit assumptions. Static prompt1 uses a full-replay
cost floor, not an assumption that every future receiver fails early.
This is a focused feasibility forecast, not statistical power or spending
authorization.

No qualification beyond these six units was executed. Proposed smallest next
batch: pending **I7/prompt1 sequence + static**, about 194 s measured-cost
projection and a proposed 300 s inclusive cap, subject to the actual remaining
ledger. It was not launched. Full qualification needs a later budget decision.

Keys, encrypted packet bytes, weights, environments and detailed private traces
are excluded. No accepted result was overwritten, no failed case was replaced,
and no commit or push was made.
