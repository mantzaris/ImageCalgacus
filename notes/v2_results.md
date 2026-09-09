# V2 bounded prospective study — reconciled results

## Decision and scope

Completed the frozen **120 stego units and 40 independent ordinary controls**, with no missing, duplicate, unexpected or invalid work identifiers. There are 100 exactly recovered, conforming carriers and 20 retained arithmetic-text capacity failures. Allocation completeness is true; all_recovered is false. No further experiments are authorized by this result.

The starting checkout was accepted revision 29d2ca2ff7e0cdf6f3a6c000d1ad7948ac8a7bc3, initially clean. The execution package SHA-256 is 85d41373c1825afb562e38e8828ab44e5dc7729313c583d64dedbea1d8e3fd15; the prospective manifest SHA-256 is 643099adf3bf2df5e62db6e49917d86d0f0c766d3e0d51b6a33dc0c62abc5e6c. The source/context manifest remains 9c20a5c11896c84d0f7accf2c5e4ad99c4e432f7bdd02bdaa2056ae3b048346f. All 105 execution-freeze files remained unchanged during model execution. All 4,827 protected historical files, including private packets/keys and old ledgers, remain byte-identical.

New work is confined to portable tests, V2 stage accounting, a dedicated continuation entry point reusing V1 helpers, CPU evidence collection and analysis. No coding, probability, tokenization, serialization, checkpoint, threshold or completion rule changed. RankCloak-derived loading/replay code and attribution remain as documented in [THIRD_PARTY.md](../THIRD_PARTY.md), including inspected revision ce853d42d6ba64065cb63c6bdfc0d825c62734cd.

The 20 frozen held-out Fashion-MNIST images and 20 Gutenberg text spans use prompt1/row1 only. Each payload/context group has one newly sealed immutable packet, shared across fixed/gated/A1 methods. Group keys and packets remain private. Order was HI1, HT1, HI2, HT2, …, HI20, HT20; within each group: fixed, gated, arithmetic, then its control. No replacement payloads, rerolls, diagnostic GPU replays, static arms, extra lossless replays or scoring passes were added.

## Executed verification and GPU evidence

| Scope | Observed result |
|---|---|
| Final clean public export CPU suite | 73 tests: 71 passed, 2 explicit prerequisite skips; 7.628s |
| Final local private CPU suite | 73/73 passed; 11.447s |
| Real Linux process integration | Model-free child passed PID/start-time and surviving-budget-marker guards |
| Public V2 verifier in clean export | 120 attempted; 100 completed/authenticated/exact; 20 recorded failures; 40 controls; complete allocation |
| Historical public revalidation | V0 10/10; V1 pilot 10 exact + 2 failures; V1.2 5 exact + 1 failure; qualification 126 exact + 26 failures across 152 units |
| Completed-run continuation | Zero new jobs/charges/outcomes; 1,846 run/ledger files unchanged; 3.653s CPU check |
| CPU analysis reproduction | Identical statistical hash, three CSV tables and two SVG plots in the clean export |
| Additional saved-file inspection | 320 strict UTF-8 files; 80 RGB carriers/control PNGs at 32×31; 40 recovered 16×16 grayscale PNGs equal their raw outputs |

The two public skips are the deliberately opt-in historical private integration and the pinned original source cache. The Linux integration passed on this host; unsupported/incoherent platforms skip only that integration. See [portability details](v1_test_portability.md). The clean export used /tmp/imagecalgacus-v2-final-public-EJPYql, contained no runs/, .runtime/, models/ or .deps-text, and did not inherit PYTHONPATH. Its absolute path is not a test dependency.

All **280 new model jobs** have allocation and positive process-specific GPU activity evidence. Text jobs verified explicit n_gpu_layers=-1 and 33/33 eligible-layer offload. Image jobs verified strict checkpoint loading, CUDA parameter/input placement, evaluation and inference modes. Jobs ran serially, receivers started in fresh processes after their sender exited, and final process inspection showed no active model jobs or GPU compute processes.

Hardware was NVIDIA RTX 5000 Ada, UUID GPU-10d1f16f-9e79-08bb-b2ba-3353c04422cf, physical GPU 1 mapped to logical CUDA 0. Existing RankCloak environments were reused: llama-cpp-python 0.3.23 CUDA text runtime and PyTorch 2.5.1+cu124 image runtime; NumPy 2.2.6, cryptography 46.0.7 and Pillow 12.3.0. No dependencies or weights were installed or changed this turn. Model hashes, device details, numerical controls, full commands and backend initialization excerpts are in the review packet.

Receiver inputs were only the saved carrier, copied declared profile/context and retained key. Private bit/interval audit paths were outputs, not receiver inputs. Source equality was checked after receiver exit by the evaluator, separately from authentication. Public review folders contain ground truth and are **not** receiver inboxes. Public verification checks saved evidence/equality and allocation; it does not repeat private-key authentication or neural decoding.

## Recovery, rate and cost

Each cell has 20 payload groups. Recovery intervals are two-sided 95% Clopper–Pearson: 20/20 gives [83.16%, 100%]; 0/20 gives [0%, 16.84%]. They are Bernoulli working-model bounds for this small, fixed, stratified allocation, not a population-representativeness or power claim.

| Carrier / method | Exact / attempted | Mean exact goodput | Mean encode / decode phase seconds | Mean charged pair seconds |
|---|---:|---:|---:|---:|
| UTF-8 / fixed | 20/20 | 3.32468 bits/token | 45.63 / 45.31 | 123.33 |
| UTF-8 / gated | 20/20 | 3.12464 bits/token | 57.31 / 57.30 | 147.29 |
| UTF-8 / arithmetic A1 | 0/20 | 0 bits/token | 398.15 / 396.01 | 826.57 |
| PNG / fixed | 20/20 | 0.25054 bits/channel | 85.27 / 85.31 | 178.18 |
| PNG / gated | 20/20 | 0.25054 bits/channel | 85.29 / 85.65 | 178.53 |
| PNG / arithmetic A1 | 20/20 | 0.25054 bits/channel | 85.59 / 85.77 | 179.01 |

PNG goodput is 0.75161 bits/pixel for all three methods. The delivered PNG is 32×31 RGB8: 992 pixels, 2,976 channel values. The shared conditioning row is not delivered as a carrier row. Image payloads are 256 raw grayscale bytes; held-out text payloads are 58–128 literal UTF-8 bytes, mean 93.2. Failed or unauthenticated transmissions receive zero exact goodput. Legacy useful_bits_per_* fields describe **offered** payload rate; they must not be mistaken for recovered goodput in failed cases.

The 292-byte packet includes 36 framing/encryption bytes and a 256-byte slot. Slot padding is zero for image payloads and averages 162.8 bytes for these text payloads. No packet size reduction or compression was used.

| Carrier / method | Mean packet-positive positions | Skipped / zero-bit positions | Completion positions | Packet-phase bits/symbol | Serialized expansion |
|---|---:|---:|---:|---:|---:|
| UTF-8 / fixed | 584 | 0 / 0 | 32 | 4.000 | 10.25× |
| UTF-8 / gated | 584 | 39.8 / 0 | 32 | 3.747 | 11.36× |
| UTF-8 / A1 | 399.4 | 0 / 1,648.6 | 0 | unavailable: incomplete | 34.11× |
| PNG / fixed | 584 | 0 / 0 | 2,392 | 4.000 | 28.21× |
| PNG / gated | 584 | 100.5 / 0 | 2,291.5 | 3.451 | 29.04× |
| PNG / A1 | 508.2 | 0 / 89.65 | 2,378.15 | 3.934 | 32.09× |

For A1, positive positions emit packet-prefix bits; zero-bit steps still consume carrier capacity. Its one PNG termination position is a subset, not another additive position. Mean discarded suffix and lookahead-zero counts are 28.9 and 29.9 bits; these are distinct, overlapping diagnostics, not extra independent payload bytes.

Packet-phase rate is 2,336 divided by packet stopping position, including skips/zero-bit steps before that stop. Including carrier completion, complete-packet rates are 3.79221 bits/token for fixed text, mean 3.56404 for gated text, and 0.78495 bits/channel (2.35484 bits/pixel) for every PNG method. Incomplete arithmetic text has no complete-packet transport rate; its recovered prefix is reported separately. Expansion uses delivered file bytes divided by canonical source bytes, not source-image PNG container bytes.

### Retained failures and arithmetic interpretation

All 20 failed transmissions have failure stage capacity: the unchanged 2,048-token cap was reached before recovering the 2,336-bit packet. No packet completed or authenticated in this cell; no source equality was claimed. Prefix recovery ranges from 581 to 2,216 bits, mean 1,456.85. Zero extension and finite-message termination were not reached in these text cases.

All 40 arithmetic audits passed the independently written interval/partition oracle, prefix-chain, source-prefix and source-window checks. All 20 PNG arithmetic transmissions reached finite termination and recovered exactly. No desynchronization, authentication rejection of a complete packet, infrastructure failure, timeout, retry or protocol correction occurred.

The inherited raw classifier labels HI5 and HI16 verified_A1_stagnation_capacity because it flags any unchanged-interval step. Their detailed evidence is narrower:

| Case | Recovered bits | Eligible surprisal | Quantized-minus-eligible surprisal | Unchanged steps / longest consecutive run |
|---|---:|---:|---:|---:|
| HI5 | 2,164 | 2,165.619 bits | −0.003476 bits | 1 / 1 |
| HI16 | 2,216 | 2,217.965 bits | −0.033058 bits | 3 / 1 |

These isolated effects do not establish sustained stagnation as the cause of the deficits. HI16's 367 consecutive zero-emission steps must not be confused with an unchanged interval: its longest unchanged run is one. HT19's successfully recovered arithmetic PNG also has one isolated unchanged step. Thus all five such steps across these three carriers are transient. Low accumulated information under the fixed cap remains the best-supported explanation for the text failures. A1's separately tested sustained finite-precision stagnation limitation remains; neither these results nor the published method's attribution erase that limitation. Full-size arithmetic text recovery remains unobserved.

## Frozen grouped analysis and exploratory scores

Before outcomes, the manifest fixed 2,000 PCG64 bootstrap draws (seed 2026090901, direction offset), resampling whole payload groups within image class or text-length band. All three methods and owned shared controls move together. Continuous and paired metrics use percentile 95% intervals. Boundary paired-binary comparisons additionally use conservative bounds from 97.5% marginal Clopper–Pearson intervals; collapsed bootstrap intervals alone are not interpreted as certainty.

Compared with fixed text, gating changes goodput by −0.2000 bits/token [−0.2192, −0.1805], charged pair time by +23.96s [20.34, 27.58], and whole-carrier eligible surprisal by −0.3912 bits/token [−0.4764, −0.3079]. PNG gated-versus-fixed charged time changes by +0.35s [−0.21, 0.98], with identical achieved goodput. Arithmetic-versus-fixed PNG time changes by +0.83s [0.38, 1.25], and mean surprisal by −0.4216 bits/channel [−0.5470, −0.3008]. All paired comparisons, including arithmetic text's zero goodput, are retained in paired_differences.csv. For binary equal-success cells, the conservative paired bound is ±19.68 percentage points despite a zero observed difference.

Twenty independent ordinary text traces ran to 2,048 tokens, the longest realized carrier in each group. Their saved matched prefixes serve fixed/gated methods. Twenty ordinary PNGs supply full-dimension matched controls. There are 120 links but only 40 independent control traces. No duplicate control artifacts or unscorable delivered cases occurred in any analysis cell; each AUC uses 20 stego artifacts and 20 unique matched control artifacts. All 20 failed text carriers are included. The previously unavailable V1 static matched prefix remains unavailable; no replacement or invented score was produced.

| Carrier / method | Mean-surprisal AUC [grouped 95% interval] | Mean-log2-rank AUC [grouped 95% interval] |
|---|---:|---:|
| UTF-8 / fixed | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| UTF-8 / gated | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| UTF-8 / A1, failed carriers | 0.380 [0.260, 0.503] | 0.360 [0.243, 0.480] |
| PNG / fixed | 0.885 [0.743, 0.985] | 0.840 [0.683, 0.965] |
| PNG / gated | 0.830 [0.700, 0.938] | 0.770 [0.630, 0.898] |
| PNG / A1 | 0.558 [0.375, 0.743] | 0.575 [0.405, 0.758] |

Higher-is-stego score directions were frozen, not selected or flipped using held-out labels. Values below 0.5 remain below 0.5. These are whole-carrier, known-model/context, inline scores—not trained detectors, unknown-observer security, human naturalness or imperceptibility evidence. Perfect empirical separation and collapsed AUC bootstrap intervals do not establish perfect population detection. Multiple exploratory comparisons and the small allocated sample warrant caution.

## Actual compute and revised forecast

| Cost term | Charged seconds |
|---|---:|
| Historical V0 | 3,163.653124 |
| Historical V1, including qualification/lossless checks | 39,995.509169 |
| V2 stego sender processes | 16,351.057174 |
| V2 fresh receiver processes | 16,307.010572 |
| V2 ordinary text controls | 7,582.818611 |
| V2 ordinary PNG controls | 1,783.641285 |
| **V2 total** | **42,024.527642 (11.67348 hours)** |
| **Whole-project actual** | **85,183.689935 (23.66214 hours)** |

The stego process total decomposes into encoding 15,144.930930s, decoding 15,107.146819s, cold loading 436.318225s and other occupied-process overhead 1,969.671772s. Controls include generation 8,964.315659s, loading 72.805638s and other occupied overhead 329.338599s. These are decompositions, not additional charges. Imports, hashing, CPU filtering while the model process is occupied, serialization and teardown remain charged.

All 280 jobs are counted once: 240 exit-0 processes and 40 expected exit-2 arithmetic capacity processes. The latter cost 16,531.319537s and were not dropped from averages. No diagnostic GPU replays, extra scoring passes or additional lossless jobs ran. CPU verification/analysis and the completed-run continuation add zero GPU seconds.

The absolute V2 allowance remains 54,000s, leaving **11,975.472358s**. V0/V1 caps and ledgers were not reset or transferred; unused V1 allowance remains 10,404.490831s. The whole-project ceiling leaves **58,816.310065s**. No prospective or qualification work remains in this authorized matrix. The established one-reserve convention is 1.25 × (actual history + remaining planned cost): 85,183.689935 + 21,295.922484 = 106,479.612419s, or **29.57767 hours**. The unused planning reserve is neither actual spend nor permission for another allocation.

## Reproduction and review

Executed model-stage commands, using the existing control interpreter:

~~~sh
python -B -m imagecalgacus.v2 --run runs/v2-prospective-001 --prepare-only
python -B -m imagecalgacus.v2 --run runs/v2-prospective-001
python -B scripts/collect_v2_review.py --run runs/v2-prospective-001
~~~

The second command was repeated after completion solely to verify idempotent continuation; no model jobs launched. Exact subprocess commands and execution identities are preserved in the public GPU job records; private packet/key paths in those records are references, not included files.

Public CPU reproduction, requiring the declared CPU dependencies but no keys/models:

~~~sh
python -B -m unittest discover -s tests -v
python -B scripts/collect_v2_review.py --verify-public artifacts/v2_review
python -B scripts/analyze_v2.py --review artifacts/v2_review
python -B scripts/finalize_v1_qualification.py --verify-public artifacts/v1_qualification_review
~~~

The analysis statistical-content hash is 05da416e55a220fe1659328ba44ffcc0dce20ad937d35f7294e25c37d64a1d61. CPU wall-time metadata can differ on reproduction. [The review packet](../artifacts/v2_review/README.md) contains carriers, recovered outputs, coverage/failures, paired tables, two plots, controls, compact audits and GPU/budget evidence. Allowlisted export and raw/hex/base64 scans exclude retained keys/packets; weights, environments, symlinks and raw private bit/interval traces are absent.

The next step is independent review of this reconciled evidence and analysis. No additional experiments, manuscript, commit, push or publication were undertaken.
