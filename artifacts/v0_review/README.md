# V0 public review packet

**Final result: 10/10 exact recoveries; V0 acceptance achieved.** Both directions ran with observed GPU inference. Total charged model-process time was 52.73 minutes of the approved 120-minute allowance. See [the execution report](../../notes/v0_results.md) for findings, commands and limitations.

This collection contains public synthetic development fixtures, generated carriers and independently recovered outputs. It is not a receiver input directory and is not evidence of imperceptibility, security against detection, broad robustness or statistical reliability.

## Inspect the artifacts

| Location | Contents |
| --- | --- |
| [fixtures](fixtures/) | The five 16×16 grayscale source PNGs and five exact UTF-8 source texts; [cases.json](fixtures/cases.json) records canonical hashes and byte counts. |
| [contexts](contexts/) | Fixed 95-byte prompt and 96-byte shared pixel-prefix row. The row is omitted from delivered PNGs. |
| [ten-001](ten-001/) | The ten final cases, one attempt per frozen payload. |
| [preliminary-001](preliminary-001/) | First successful I1/T1 examples; separate development attempts, not extra independent evaluation cases. |
| [preflight](preflight/) | Text/image GPU checks, checkpoint provenance and the first ordinary 32×32 image. |
| [results.jsonl](results.jsonl) | All 12 stego attempts, marked by phase; filter `phase == "ten"` for the ten-case evaluation. |
| [acceptance.json](acceptance.json) | Count, budget, input-boundary and frozen-source acceptance checks. |

For each **I** case: open `source.png`, `carrier.txt`, `recovered.png`; `recovered.gray` contains the exact 256 canonical pixel bytes. For each **T** case: open `source.txt`, `carrier.png`, `recovered.txt`. Every directory includes `sender.json`, `receiver.json` and `evaluation.json`.

Text carriers contain 616 tokens, including 32 completion tokens. PNG carriers are width 32 × height 31, RGB8: 992 pixels or 2,976 channel values, not 2,976 pixels. Both carry the same 292-byte authenticated packet through 584 fixed-rank symbols. PNG completion adds 2,392 channels.

## Audit the evidence

- [gpu_evidence.json](gpu_evidence.json): actual subprocess commands/PIDs, conservative per-process wall-time charges and per-process GPU-activity observations for all 26 jobs. Backend initialization/placement evidence is in preflight and per-case reports; [the initialization excerpt](preflight/text_initialization_excerpt.txt) preserves the actual full-offload/batch/buffer log lines. Large raw logs remain local.
- [receiver_input_checks.json](receiver_input_checks.json): only carrier, profile, context and key in each receiver input directory; matching fixed contexts and profiles. This is data-flow separation, not an OS sandbox.
- [focused_tests.json](focused_tests.json): final CPU test command/output; 16 focused tests passed. No CPU neural inference.
- [environment.json](environment.json), [profile.json](profile.json), [source_manifest.json](source_manifest.json): runtime/dependency versions, explicit host/model configuration, source/config/test/script hashes.
- [ten-001/compute_projection.json](ten-001/compute_projection.json): the measured pre-run estimate and reserve. Application source remained frozen across all ten cases.

The root results JSONL rewrites artifact/evidence paths relative to this collection. Raw per-case reports retain original execution paths for provenance. Generation/replay timings exclude cold model loading; charged process durations include it. Repeated CPU evaluation or copying does not add attempts.

Cryptographic run keys, model weights, private environments and full diagnostic dumps are excluded. A local byte-level scan checked this collection against every retained run key. Keys remain in private ignored `runs/` for later decoding; they are never derived from sampling seeds.

Independent replay requires the retained local key and declared model assets. Stage only the four permitted inputs in a new receiver input directory, use a fresh output/report path, and follow [the GPU-wrapped receiver commands](../../README.md). Do not pass this collection or an evaluator manifest to the receiver. Another host must establish its own compatible GPU preflight; CPU/partial-offload fallback is forbidden.

No V1/V2 methods or study results are included.
