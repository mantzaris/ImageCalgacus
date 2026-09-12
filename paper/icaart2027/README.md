# ICAART 2027 complete first submission draft

**Exact Bidirectional Steganographic Transport with Language and Pixel Autoregressive Models**

Prepared as an anonymous Regular Paper in Area 2, Artificial Intelligence, for local author review. Revised on 11 September 2026 from reviewed commit `9f91143`. This editorial operation did not submit, upload, commit or push anything.

- [Main submission PDF](ICAART2027_submission.pdf), 12 A4 pages, including references.
- [Companion PDF](ICAART2027_supplement.pdf), 8 A4 pages. Separate supplementary-upload status is unconfirmed.
- [Self-contained source ZIP](ICAART2027_source.zip), compilation-tested outside the repository.
- Both actual worked examples are **Figure 1A and 1B on main page 3**, using the unchanged retained figure.
- [Author review and policy decisions](AUTHOR_REVIEW.md).
- [Numerical/preservation verification](verification.json), [archive verification](source_archive_verification.json), [page inspection](visual_inspection.md), [primary reference checks](reference_verification.md), [editorial revision and policy recheck](editorial_revision.json).

## Contribution

We develop a common authenticated artifact-transport protocol across language and pixel autoregressive models. A paired three-coder study establishes exact bidirectional recovery and exposes the interaction of serialization, finite capacity and known-model detection. Repeated PNG scoring measures one specified context mismatch. Exact matched development executions establish a behavior-preserving CUDA graph speedup. The paper distinguishes this integration and empirical contribution from earlier rank transfer, bounded coding, tokenization verification, arithmetic steganography and standard CUDA graph infrastructure.

The main results are 20/20 fixed and gated recoveries in both directions, 20/20 arithmetic PNG recoveries and 0/20 arithmetic text recoveries under the fixed cap. Fixed PNG primary AUC decreases from 0.8850 to 0.6975 under the specified mismatch. The development GPU headline is a 5.133075499-fold matched reduction in charged encode-plus-decode latency, not a replacement for prospective timings.

## Build and verification

From the repository root, using Python 3 and the existing TeX Live packages:

```sh
python -B paper/icaart2027/build.py
python -B paper/icaart2027/package_source.py
```

The archive's standalone command is `python -B build.py`. No repository, network, model weights, private files or GPU is needed. Standard installed TeX packages are listed in [BUILD_README.md](BUILD_README.md). The archive contains only the required TeX/BibTeX sources, figure PDFs, tables, unmodified template files and build instructions, not examples, numerical inventories, author notes or caches.

Optional manuscript-only refresh from unchanged retained evidence:

```sh
python -B paper/icaart2027/prepare_assets.py
python -B paper/icaart2027/build_tables.py
python -B paper/icaart2027/build.py
```

Run the focused saved-evidence and numerical audit with the established CPU analysis environment. On the execution host this command ran successfully:

```sh
../llm-rankcloak/.venv/bin/python -B paper/icaart2027/verify.py
```

The script needs the repository's public retained evidence and existing NumPy/Pillow/cryptography dependencies. It invokes the existing public qualification, V2 and benchmark verifiers. It reproduces the accepted context analysis while redirecting its report into this manuscript directory, so original review files are not rewritten. It checks existing ledgers only if present. No neural inference or private-key authentication is performed. Public verification checks source equality, hashes, pairing, recorded authentication and completeness; fresh receiver reproduction is a different operation requiring the private execution environment and is not part of manuscript preparation.

## Results map

All accepted publication exports remain byte-unchanged. Copied asset hashes and source paths are in [data/asset_provenance.json](data/asset_provenance.json). Additional table variants change layout only, using original unrounded CSVs. The retained vector process diagram is now Figure S1 in the companion. Figure 1 in the main paper shows the actual artifacts without modifying its PDF, pixels or carrier text.

| Accepted result or asset | Main paper | Companion / supporting location |
|---|---|---|
| Implemented packet, model and receiver contract | Section 3, Table 1; actual examples in Figure 1 | Figure S1 process diagram, S3 interval details, S7 runtime identities |
| Publication Figure 1, real bidirectional examples | **Figure 1A–B, page 3**, Section 3.1, `fig:examples` | Complete [text carrier](examples/HI1-prompt1-fixed/carrier.txt) and [PNG carrier](examples/HT1-row1-fixed/carrier.png) are retained for local author inspection, not claimed submission attachments |
| Publication Figure 2, all six recovery/rate cells | Figure 2, Table 2, Section 5.1 | Table S1 with original goodput intervals and timing |
| Publication Figure 3, correct-context score distributions | Principal six primary AUCs in Section 5.3 | Figure S2, Table S2 with both scores and counts |
| Publication Figure 4, GPU performance | Figure 4, Section 5.5 | Table S6 and Section S6, all five combinations and timing boundaries |
| Publication Figure S1, arithmetic information accumulation | Capacity result and diagnosis in Section 5.2 | Figure S3, Section S3, retained checkpoint/endpoint data |
| Publication Figure S2, paired sequence/static comparison | Main Section 6 gives 40/40 versus 22/40 | Figure S4 and Section S4, two prompts over 20 payloads |
| Publication Table 1, specification | Table 1 and Sections 3–4 | Full source/context/model inventories in `data/` |
| Publication Table 2, recovery/goodput/runtime | Table 2 | Table S1; original prospective times preserved |
| Publication Table 3, both detection scores | Primary findings in Section 5.3 | Table S2, unique-control and failed-carrier counts |
| Publication Table 4, all GPU combinations | Fixed nine-comparison aggregate in Figure 4 | Table S6; 11 comparisons and 22 exact recoveries |
| Publication Table S1, framing and completion overhead | Section 5.1 gives main rates/packet overhead | Table S3, exact source CSV and Section S3 |
| Accepted paired method comparisons | Rate/time interpretation in Section 5 | S2 paragraphs, `data/accepted_paired_differences.json` |
| PNG context-AUC figure | Figure 3, Section 5.4, `fig:png-context-auc` | Original PDF copied unchanged |
| Full context primary/secondary comparison | Principal interpretation in Section 5.4 | Table S4, `tab:png-context-scores` |
| Score-shift addendum | Descriptive gap interpretation in Section 5.4 | Figure S5, Table S5, `fig:png-score-shifts` |
| Twenty development lossless PNG replays and UTF-8 byte checks | Brief supporting discussion, Section 6 | S4, qualification evidence; no new observations |
| Unavailable historical static matched-control prefix | Not used to claim a score | Explicitly retained as unavailable in S4 |
| CPU verification, source caches and execution checkpoints | Not a main result | Existing implementation notes and review records |

The main caption explicitly explains the figure's original “full file linked in caption” note as referring to locally retained material, not an available review link. It identifies the incomplete text excerpt, canonical pixel endpoint, complete literal text, receiver inputs and withheld row. No `examples/` path appears in the main or companion PDF as a reviewer-access claim. The examples are not duplicated in the companion.

Main labels and numbering also appear in the preserved [results integration directory](../results/README.md). There are four main figures and two main tables, plus five companion figures and six companion tables. The main PDF includes all indispensable methods, sample definitions, principal findings and limitations without requiring the companion to be reviewed.

## Template, length and editorial checks

The official archive was downloaded on 10 September 2026 from [SCITEPRESS](https://www.scitepress.org/documents/SCITEPRESS_Conference_Latex.zip), as linked by [ICAART Templates](https://icaart.scitevents.org/Templates.aspx). The link, archive and all six supplied files were checked again on 11 September 2026 and match their original hashes. Class, typography, margins, spacing and bibliography style are unmodified. [Template provenance](template/provenance.json) records the archive and exact supplied-file hashes. Body is 10-point, references/tables/captions use the supplied 9-point convention. No margin/font/spacing workaround was used to obtain 12 pages.

The [current Guidelines](https://icaart.scitevents.org/Guidelines.aspx), rechecked on 11 September 2026, specify 10,000–50,000 non-whitespace characters for Regular Paper submission, including references, figures, tables and appendices. The revised main PDF has **39,713 extracted non-whitespace characters**. Its deliberately conservative **42,596-character estimate** adds all four external figures' extractable text again (1,883 characters), plus 1,000 for possible extraction losses. The process diagram is now outside the main submission and adds zero to this count. Figure text, tables and references are already present in the main extraction, so the extra allowance errs upward. This is not an official portal count, and no official figure-to-character conversion was identified. The unchanged abstract is **176 words**, within the template's 70–200 range. The companion has 21,645 extracted non-whitespace characters and is not counted as an approved submitted appendix.

All pages were rendered at 130 dpi and inspected for text/figure readability, labels, overflow, equation breaks, bibliography and float placement. The example is legible at full manuscript width. Standard float placement resolved the companion overflow introduced by moving the diagram. The drafting footnote was shortened to avoid a stranded word, while its section-level citation and the full disclosure remain. No unresolved references, citations or overfull boxes remain. Only author-review documents discuss submission-policy uncertainties and actual authorship decisions. Prose was reviewed for unnecessary dash punctuation, semicolons and colons; mathematical minus signs, numerical ranges, identifiers, exact reference titles and accepted figure labels were preserved.

## Provenance, anonymity and preservation

This revision starts at the clean reviewed checkout `9f911438755ac8fff5ae9b6ea9f30850efb6b6da`, with no intervening commits. Figure 1 was moved intact into Method, the generic diagram moved to the companion, and repeated attribution, observer-scope and performance caveats were consolidated across the Introduction, Related Work, Results and Discussion. Essential protocol, experimental design, six outcomes, numerical tables and uncertainty estimates remain. The reviewed main count was 41,873 extracted / 45,136 conservative; those historical values are retained in [the revision record](editorial_revision.json).

The original manuscript preparation started at repository revision `bdecbf2f4e524885ba7408ec282d9cf47d6a779b`, with a clean worktree. Since the reviewed GPU benchmark revision `5e08a8b`, commits `cdff18c`, `c2effbb` and `bdecbf2` added the accepted publication exports, PNG context study and score-shift integration. Their evidence is incorporated without repeating inference. New draft/code identities are recorded separately from historical execution identities. Existing `paper/results/` prose and figures were incorporated. No prior experiment is relabeled as having run the manuscript code.

The anonymous PDFs have no author block, affiliation, email, acknowledgements, project repository link or author metadata. Relevant prior work remains cited normally in third person. Public project history and the exact scientific protocol identifier can still permit inference of authorship, as noted in [AUTHOR_REVIEW.md](AUTHOR_REVIEW.md). The compilation-only ZIP excludes machine-local inventories, rows, keys and private material. `data/protocol_identities.json` is an exact retained inventory for local author review and is deliberately not in that ZIP.

The preservation audit checks 3,700 accepted public evidence/configuration/plan/note files and five unchanged GPU ledgers. Historical cumulative occupied-process accounting remains **88,975.067936 seconds** (24.7153 hours). Manuscript preparation adds **0 GPU seconds**. No tests or experiments were rerun to improve outcomes. Saved-evidence CPU checks do not constitute new transmissions or fresh model replay.

## Author decisions before upload

Read [AUTHOR_REVIEW.md](AUTHOR_REVIEW.md). Supply the actual author list and confirm originality/overlap, funding and disclosure obligations. Current official pages conflict between AI disclosure in acknowledgements and omission of acknowledgements for anonymity. The draft uses an anonymous AI Assistance Disclosure plus section-level tool citations, consistent with the AI page's alternative placement; confirm this resolution with the venue. A separate Regular Paper supplementary-upload permission is unverified. No public posting or submission is authorized here.
