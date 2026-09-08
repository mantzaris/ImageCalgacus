# V1.2 — source preparation, static comparison, first qualification batch

8 September 2026. **Preparation and the development-only comparison arm are ready.**
All six authorized units ran: **five exact recoveries and one correctly recorded
static tokenization-drift failure**. Both sequence-arm cases and both PNG cases
passed. V1 is **not fully qualified**; no V2, held-out generation, additional
calibration/control jobs, arithmetic reruns, commits or pushes occurred.

## Starting point and preservation

Started at pushed revision `aea21e0179b7c3a5cc5ba3ece73e2d585e058495`, with a
clean worktree. Applicable repository/ancestor instructions were checked (no
AGENTS.md found); both plans, V1.1 notes/review, current code, tests and retained
records were inspected. Initial package hash was
`ea7857902e3a127f2ef014f907dc41a775290142ef9ff5e6ac27fa574442638c`.
The inference package was frozen before the batch at
`886f953c9020ca89882a1a33d48661df5fdba020f2d1eca936955860ad070d70`
and remained unchanged throughout all twelve jobs.

All **725 protected files** still match their starting hashes, including accepted
review packets, fixtures/contexts/profiles, old results/logs and retained private
keys. The original V1 ledger prefix is unchanged; twelve jobs were appended to
that same ledger. V0 still costs 3,163.653124 seconds. [Preservation evidence](../artifacts/v1_2_review/preservation.json).
No earlier observation is superseded. In particular, the two arithmetic text
capacity failures and the separate A1 stagnation limitation remain as diagnosed
in [V1.1](v1_1_results.md); neither coder was modified or rerun.

## Reproducible CPU preparation

[Source manifest](../data/qualification_v1/manifest.json), SHA-256
`9c20a5c11896c84d0f7accf2c5e4ad99c4e432f7bdd02bdaa2056ae3b048346f`,
contains **80 sources**: 20 images/20 texts in development and the same held-out
counts. Existing five fixtures per direction are byte-preserved. Added images
come from Fashion-MNIST training IDX data; held-out test images are two per class.
All images are literal L-mode 16×16/256-byte payloads after pinned Pillow BOX
28→16 resizing. Added texts are literal Gutenberg 11/84 spans; held-out uses
nonoverlapping 1342/1661 spans. Each split has ten texts in each 32–64/65–128-byte
band; the accepted non-ASCII fixture is preserved.

The reproducible rule uses class round-robin/smallest unused original image
index and alternating books/first unused narrative paragraph, with longest
whole-word valid UTF-8 endings in each band. It checks original/canonical
duplicates, literal original byte offsets, disjoint splits and exact fixture
preservation. No duplicate candidate was excluded in this selection. Front
matter and non-prose exclusions are rules, not a claim of zero excluded
paragraphs. Narrative anchors exclude the Austen editorial preface. See the
[preparation details and attribution](../data/qualification_v1/README.md).
The frozen lock records all URLs, archive hashes, official Fashion-MNIST MD5s,
source revision, ebook edition headers and required terms. Raw downloads remain
in ignored `.runtime/source_cache`; there were no dependency/weight downloads.

Commands actually run successfully, with the existing control/image interpreter:

```sh
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/prepare_v1_sources.py --output data/qualification_v1
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/prepare_v1_sources.py --output .runtime/v1_2/source-reproduction
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/prepare_v1_qualification.py
```

The original acquisition used `--acquire`. Two final preparations produced
identical manifests and all generated payload/context/terms bytes. New output
directories are mandatory; commands deliberately refuse to overwrite them.
Upstream hash changes fail rather than silently selecting a new edition.

Prompt1/row1 retain their original bytes. Prompt2 is exactly
“Explain how a home cook prepares a simple vegetable soup. Use continuous prose.”
without a newline; hash
`44d6ae29a3ae87ee635cb8096a353c1f16d79d5aee912d50e180ead10b3dd80f`.
Row2 is 96 independent RGB8 bytes from NumPy PCG64(2002), constructed on CPU
without payload/model/appearance dependence; hash
`c7f5500001d4376a74183225a88ececc5541e2bde1d79a30961ff458073ae5e1`.
Sampling/preparation seeds never determine encryption randomness.

## Allocation and credit reconciliation

[Allocation](../configs/v1_qualification.json), hash
`60e129121f585ad431d2fee10351a24d5e419a10bfc171c813afb33b0cb41569`,
contains concrete work IDs, purpose, profile/context hashes and pending/credited
records. Text-filter arm is part of the scientific definition and new work ID.
Legacy case/work IDs are retained exactly, with an explicit credit reference and
original execution source hash. Allocation-level/source-definition hashes
identify this checkpoint, not a claim that old jobs ran this new source.

| Qualification arm | Total | Accepted pilot credit | This batch outcomes | Still pending |
| --- | ---: | ---: | ---: | ---: |
| Fixed text, sequence | 40 | 2 | 2 exact | 36 |
| Fixed text, static | 40 | 0 | 1 exact + 1 drift failure | 38 |
| Fixed PNG | 40 | 2 | 2 exact | 36 |
| Gated/arithmetic timing | 32 | 8 | 0 | 24 |
| Ordinary development traces | 16 | 4 | 0 | 12 |
| Shared controls, upper allocation | 48 | 2 | 0 | 46 |

Thus **152−12=140** stego units were pending initially, and **134** remain.
The timing allocation is four payloads × two contexts × two new methods per
modality: I1/I5/I6/I7 and T1/T3/T6/T7, chosen before new carriers. Ordinary traces
are four/context/modality; pending traces audit the frozen thresholds, never
recalibrate them. Controls are twelve/context/modality associated with the first
twelve payload IDs; shared method prefixes are not extra control replicates.
Historical controls used by multiple pilot payloads are each credited once.
V0 repeats and diagnostic replays receive no credit. The new batch has two
distinct payloads and four payload/context groups, not six independent payloads.
[Append-only credit events](../artifacts/v1_2_review/qualification_events.jsonl)
and [coverage](../artifacts/v1_2_review/qualification_coverage.json) supplement
the immutable allocation instead of rewriting its initial pending state.

Every payload/context group keeps one immutable encrypted packet across its
methods/arms. New groups use a fresh run key and fresh random nonces. For a
legacy group's pending arm, transport its already sealed sender-private packet;
do not encrypt new plaintext with an old run key or resume an encryption stream.
This is ciphertext transport reuse, not another encryption. The original packet
and work identity are prerequisites for claiming a paired legacy credit.

## Static arm: precise implementation difference

Adapted the **singleton criterion** from RankCloak
`rankcloak/revision_protocol.py::build_round_trip_stable_mask`, revision
`ce853d42d6ba64065cb63c6bdfc0d825c62734cd`; MIT attribution remains in
[THIRD_PARTY.md](../THIRD_PARTY.md). Re-inspected its exact-byte helpers,
model loader, reset/incremental replay and GPU configuration. No whole upstream
pipeline or implicit sibling import was added.

`TextBackend.eligible_piece` checks `T(D([v])) == [v]` in static mode,
versus the unchanged complete-prefix test in sequence mode. Singleton results
are cached lazily for encountered candidates, equivalent to the context-free
mask without a full-vocabulary startup pass. Both arms first take exactly the
same top 256, then retain this project's same special/empty/strict-UTF-8
exclusions, float64 normalization, rank order/ID tie break, prompt boundary and
completion sampling. Upstream's different safe-text policy was not imported.
The default profile is unchanged; only
[the development static profile](../configs/v1_fixed_static.json) opts in.
Gated/arithmetic and image use of that option is rejected.

Serialization always checks exact detokenized bytes, strict UTF-8 and the pinned
piece-concatenation contract. Sequence mode still rejects final tokenization
drift. Static mode **saves those bytes unchanged**, even if their fresh
tokenization differs. Sender diagnostics publish only counts/first mismatch,
not token sequences. Receivers reconstruct solely from saved bytes and their
declared arm; no repair or normalization is performed.

The existing runner gained one bounded qualification entry point for **new packet groups**. It creates fresh group packets and is not a resumable scheduler. For pending arms of already sealed groups (including I1/I5 and the new I6/T6 groups), use the existing sender `--prepared-packet --key` transport path with the recorded packet identity; do not feed such groups back through the new-group preparation branch. No generic continuation framework was added. Each sender
exits before its fresh receiver starts. Receiver input directories contain
exactly carrier, profile, context and key; source/reference/packet/diagnostic
files remain outside. The independent evaluator compares original/recovered
bytes. It records sender/receiver completion separately, delivered retokenized
counts, and static drift failure classification; early-failure replay time is
now retained. No probability, coding, completion or arithmetic rule changed.

## Verification and six-case execution

**52 CPU tests passed** before GPU execution; the final rerun also passed all 52
in 11.291 seconds. Eight new tests cover singleton/prefix differences, drift
serialization, strict sequence rejection, saved-bytes-only receiver failure,
profile bounds, source indices/offsets/duplicates/fixture preservation,
reproduction and distinct paired work IDs/coverage.
[Final test transcript](../artifacts/v1_2_review/cpu_tests_final.txt).
Read-only public revalidation still gives V0 **10/10** and V1 **ten exact plus
two capacity failures**, complete allocations without changing their carriers.

The frozen [batch](../configs/v1_2_batch.json) selected I6 (Fashion training
index 1, class 0) and T6 (Gutenberg 11 bytes [1570,1632), **62 literal bytes**,
including the original line ending). Six senders and six fresh receivers ran:

```sh
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.v1_pilot --qualification-batch configs/v1_2_batch.json --new-run runs/v1-qualification-001 --packet-run runs/v1-qualification-packets-001
```

The existing budget wrapper charged stage V1 and enforced per-child hard limits
110/130/130/150/110/110 seconds, each again for decoding. Their sum, **1,480 s**,
fit the **1,675.213 s** starting balance, with 195.213 s outside those limits.
Whole child occupancy includes load/hash checks, lazy mask construction,
CPU filtering, neural inference, serialization and teardown. Complete groups
were checked before starting, with receiver/teardown headroom. No retry occurred.
All exact child commands and PIDs are in [GPU jobs](../artifacts/v1_2_review/gpu_jobs.json).

| Case | Encode / replay operation s | Charged sender / receiver s | Delivered size | Outcome |
| --- | ---: | ---: | --- | --- |
| I6 prompt1 sequence | 41.266 / 41.126 | 57.009 / 56.786 | 2,177 B; 616 tokens | Exact |
| I6 prompt1 static | 14.845 / 6.287 | 30.434 / 22.415 | 2,708 B; 613 retokenized tokens | Drift failure |
| I6 prompt2 sequence | 42.417 / 42.590 | 58.149 / 58.938 | 2,797 B; 616 tokens | Exact |
| I6 prompt2 static | 14.700 / 14.679 | 30.481 / 30.531 | 2,925 B; 616 tokens | Exact |
| T6 row1 fixed | 85.936 / 84.715 | 89.709 / 88.396 | 2,220 B PNG | Exact |
| T6 row2 fixed | 84.576 / 85.649 | 88.294 / 89.398 | 2,475 B PNG | Exact |

All senders completed the 584-position packet and prescribed completion.
Text senders generated 616 tokens; PNGs contain 992 pixels/2,976 channels with
2,392 completion channels. Five receivers authenticated, completed and matched
source bytes exactly. The failed static receiver reconstructed 613 tokens from
the actual file, diverged at zero-based position 247 (matching the sender-side
first mismatch), and failed eligible-symbol replay after 988 bits. It neither
authenticated nor produced recovered bytes. Its sender packet/carrier completed;
its receiver packet/carrier did not. Exit 1 is an expected comparison failure
here, not hidden infrastructure success. The second static carrier had no drift
and fully replayed. [Public saved carriers and recovered outputs](../artifacts/v1_2_review/cases/).

Both backends demonstrably used the existing RTX 5000 Ada, UUID
`GPU-10d1f16f-9e79-08bb-b2ba-3353c04422cf`, physical PCI 09:00/logical CUDA 0,
driver 590.48.01. Every text initialization reported **33/33** layers offloaded,
with `n_gpu_layers=-1`, logits_all and batch/ubatch 1. llama-cpp-python 0.3.23,
its CUDA libraries, complete reset/incremental replay and numerical controls
are unchanged. PixelCNN++ retained strict loading, CUDA parameters/inputs,
eval/inference mode and pinned float32 controls in PyTorch 2.5.1+cu124.
All twelve PIDs showed GPU allocation/activity (text peak SM 94–98%, image
26–51%). Models remain the exact accepted GGUF and PixelCNN++ hashes recorded
in profiles. No CPU/partial-offload fallback, environment installation or model
change occurred. [Initialization evidence](../artifacts/v1_2_review/backend_initialization.json).

## Accounting, forecast and limits

Actual new GPU charge: **700.539619 s** (0.194594 h): generation 283.739344,
replay 275.044272, backend cold loading 25.438007, other occupied process
setup/hash checks/teardown 116.317996. No extra profiling, calibration, control,
lossless diagnostic or arithmetic job was run.

| Historical stage | Charged seconds |
| --- | ---: |
| V0, unchanged | 3,163.653124 |
| Original V1 checkpoint | 4,690.205214 |
| V1.1 diagnostics | 834.581835 |
| V1.2 batch | 700.539619 |
| V1 ledger total / remaining to 7,200 | 6,225.326668 / **974.673332** |
| Cumulative project history | 9,388.979792 |

The CPU-only projection command actually run was:

```sh
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/project_v1_compute.py --qualification-results runs/v1-qualification-001/results.jsonl --output artifacts/v1_2_review/compute_projection.json
```

[Projection](../artifacts/v1_2_review/compute_projection.json) uses original
method-specific costs **including both arithmetic capacity failures**, adds the
new fixed context1 samples for main-study means, and uses separate measured
context2/static cells for remaining development. Second-context gated/arithmetic
and ordinary/control timings remain first-context same-method/modality
assumptions. For prompt1 static, an early failure does not price every future
replay: its planning cost uses the maximum of observed early replay,
sender-length occupancy and the observed full prompt2 static replay. This adds
154.212 s over naively projecting early failure across the remaining static
cases. Each new context/static cell has only one observed payload.

| Prospective cost, unreserved | Seconds | Hours |
| --- | ---: | ---: |
| Remaining 134 stego qualification units | 20,918.365 | 5.811 |
| Remaining 12 ordinary traces | 1,333.523 | 0.370 |
| Remaining up to 46 controls | 10,573.219 | 2.937 |
| **Remaining qualification subtotal** | **32,825.107** | **9.118** |
| Main 120 units: generation / replay | 15,045.571 / 14,968.518 | 4.179 / 4.158 |
| Main loading / other occupied process time | 435.264 / 1,899.315 | 0.121 / 0.528 |
| Main up to 40 independent shared controls | 9,194.104 | 2.554 |
| Required 20 additional lossless PNG replays | 1,761.238 | 0.489 |
| History + all prospective work | 85,518.097 | 23.755 |
| One 25% reserve | 21,379.524 | 5.939 |
| **Whole project with reserve** | **106,897.621** | **29.694** |

The standalone remaining-development estimate with 25% headroom is **11.398 h**;
it is not added again to the whole-project reserve. Likelihood summaries are
already collected inline; no new neural scoring job is assumed. UTF-8 byte
roundtrips, PNG rewrite/pixel equality and JSON aggregation are CPU work; the
twenty additional fresh PNG replays remain separate future jobs. This batch
enters spent history once and is removed from pending units. Diagnostic replay
is never an experimental unit or unrelated qualification credit.

The point forecast falls from V1.1's 30.806 h to **29.694 h**, mainly by replacing
the static sequence-cost proxy with measurements. It remains below the 40 h
ceiling **conditionally**, not as an authorization or throughput/power guarantee.
Full remaining qualification cannot fit the 974.673 s phase balance: it needs
about **31,850.434 additional seconds (8.847 h), unreserved**, beyond that
balance. Runtime uncertainty is highest for unseen context/method trajectories
and ordinary controls; two text arithmetic failures are not universal capacity
claims.

## Failures, limitations and next checkpoint

CPU preparation first stopped on a Gutenberg license heading containing ™.
That incomplete output was preserved under
`.runtime/v1_2/source-preparation-001`; license handling and front-matter
boundaries were corrected before the frozen source selection/model work.
An allocation guard also caught the historical calibration/control profile
difference; explicit original profiles were used before freeze. An initial
read-only V0 validation used the wrong phase label (`ten-001` instead of
`ten`) and correctly reported missing records; the corrected strict validation
passed 10/10. These were CPU preparation/invocation corrections, not new
observations or carrier retries. The static drift failure is retained, not fixed
or superseded.

Remaining V1 conditions are exactly the pending allocation above: all 40
sequence comparisons and 40 fixed PNG recoveries, all static outcomes,
24 remaining gated/arithmetic timing units with honest capacity classification,
12 ordinary audits and up to 46 controls; retain the independent A1 finite-stream
checks/known limitation, required lossless checks, and a final measured protocol/
compute freeze. No optional sweeps or detector work were added. The main study
stays 20 held-out payloads/direction, one existing context, three methods and
up to 40 shared controls. No broad reliability, imperceptibility, robustness
or statistical-power claim is established.

Smallest proposed next bounded batch: **I7/prompt1 fixed sequence + static**,
one intact already-pending pair with a new group packet. Using the older
maximum sequence pair (132.733 s) plus a full static pair (~61 s) gives about
194 s; propose a **300 s inclusive bound** with receiver/headroom reserved.
It fits the current remainder if separately authorized, but was **not run**.
Do not proceed to V2; further qualification beyond the existing remainder needs
an explicit budget decision.
