# ICAART 2027 single-PDF submission draft

**Exact Bidirectional Steganographic Transport with Language and Pixel Autoregressive Models**

The sole proposed review artifact is [ICAART2027_submission.pdf](ICAART2027_submission.pdf), an anonymous Regular Paper in Artificial Intelligence. The main paper stands alone. Reviewers are not assumed to receive the companion, source archive, local examples or repository evidence.

- Main PDF: **12 pages**, including references; **41,500 extracted** and **44,135 conservatively estimated non-whitespace characters**; **180-word abstract**.
- [Compilation source ZIP](ICAART2027_source.zip), independently rebuilt and verified.
- [Companion PDF](ICAART2027_supplement.pdf), 11 pages, maintained as optional author material. No separate supplementary submission route is assumed.
- [Author decisions](AUTHOR_REVIEW.md), [verification](verification.json), [archive check](source_archive_verification.json), [visual inspection](visual_inspection.md), [reference verification](reference_verification.md), [asset notices](ASSET_NOTICES.md).
- [Finalization note](../../notes/icaart_single_pdf_finalization.md) and [starting-state record](data/single_pdf_start.json).

## Canonical single-file manuscript

Edit [main.tex](main.tex) directly. It contains the preamble and macros, title and abstract, all sections, equations, figure environments and captions, three complete table definitions, disclosure and the twenty formatted bibliography entries. Origin comments mark the inlined material. Explicit boundary spaces preserve the former file-loading whitespace. No manuscript-fragment commands or external bibliography source are needed.

From the repository root, compile only the submission with:

```sh
python -B paper/icaart2027/build.py --target main
```

The remaining local compilation dependencies are `template/article.cls`, `template/SCITEPRESS.sty`, `template/apalike.sty` and four figure PDFs in `figures/`: `figure1_transport_submission.pdf`, `cover_transport_submission.pdf`, `figure2_recovery_rate.pdf` and `context_auc.pdf`. Standard installed LaTeX packages are also required. No BibTeX run, `.bib`, `.bbl`, preamble file, section file or table fragment is read by the main build.

The ten old main-only sections and two main-only table fragments have been removed after exact inlining. They remain recoverable in Git history. The companion remains separate. Its external `preamble.tex`, `sections/cover_supplement.tex`, `figures/method_diagram.tex` and six companion table fragments are retained only for that document. `references.bib` and `template/apalike.bst` serve the companion and reference maintenance. Changes to the BibTeX database do not automatically change the main paper's inlined bibliography. See [BUILD_README.md](BUILD_README.md) for maintenance and direct pdfLaTeX commands.

The build never reconstructs or overwrites `main.tex`. `build_tables.py` now generates companion tables only. Retained publication table copies are evidence inputs, not alternative editable main tables.

Consolidation starts at `0c7296327c0131201b3372a9c5bab70eddba4f0d`. That commit's later abstract edit is preserved verbatim. Its committed PDF predated the edit, so comparison uses a fresh build of the actual starting source. [Consolidation verification](consolidation_verification.json) proves exact text, bibliography, citation/label and 144-dpi page-pixel equivalence, including the unchanged companion. [Source-organization note](../../notes/icaart_source_consolidation.md) records the bounded change.

## Contribution and principal results

The shared authenticated protocol transports canonical image bytes through generated text and literal text through generated PNGs or bounded photograph changes. Fresh receivers reconstruct solely from delivered artifacts and declared inputs. The controlled comparison makes serialization, capacity, observer knowledge and execution cost assessable together.

All six original prospective outcomes remain **20/20, 20/20, 0/20** for fixed/gated/A1 text carriers and **20/20 in each method** for generated PNGs. Arithmetic text failures remain capacity outcomes. Fixed-PNG primary AUC changes from 0.8850 to 0.6975 under one frozen row mismatch, with paired change −0.1875 [−0.2775, −0.1000]. Those are repeated scores on the same 80 PNGs, not photograph detection or new transmissions.

The development GPU benchmark retains **5.133075499×** matched fixed-rank improvement, over nine timing pairs on three payloads, with exact checked probability/carrier/recovery equivalence. Original prospective timings are unchanged. The photograph comparison retains **20/20 held-out recoveries per arm**, mean PSNR 70.255 versus 70.398 dB and SSIM 0.9999664 versus 0.9999688 for model ranks versus parity. Distinct learned partitions demonstrate no recovery, fidelity or runtime advantage over that simple baseline.

## Results and dependency map

| Finding or contract | Location inside the main PDF | Optional detail, not needed to assess the main claim |
|---|---|---|
| Image → saved text → canonical image | Figure 1A, page 3; Section 3.1 | Full author-side carrier retained locally, not promised to reviewers |
| Literal text → generated PNG → text | Figure 1B, page 3 | Retained source/carrier/recovery evidence |
| Text → photograph → text, cover comparison | Figure 2A–C, page 6; Section 3.5 | First three covers/differences in companion Figure S7 |
| Exact packet, padding, receiver boundary, RGB conditionals | Sections 3.1–3.2 | Companion Figure S1 and S3 |
| Three coders, A1 termination and separate stagnation limit | Sections 3.3–3.4 and 5.2 | Companion arithmetic Figure S3 |
| Invariant context, rank parity, keyed placement, distortion bound | Section 3.5 | Companion S7, unchanged photograph review |
| Sources, allocations, pairing, model/GPU and uncertainty | Section 4 and Table 1, page 7 | Detailed inventories remain author-side |
| Six recovery/rate/runtime cells | Figure 3, page 10; Table 2, page 9; Section 5.1 | Companion Table S1 |
| Both known-model detection scores | Section 5.3, all counts and AUCs/intervals | Companion Figure S2/Table S2 |
| PNG observer context mismatch and descriptive score shifts | Figure 4, page 11; Section 5.4 | Companion Figure S5, Tables S4–S5 |
| Exact GPU benchmark, timing boundary and memory tradeoff | Sections 4.5 and 5.5 | Companion Figure S6/Table S6 |
| Photograph fidelity, recovery and simple parity outcome | Section 5.6; Table 3, page 11 | Per-case photograph exports |
| Sequence/static development comparison, lossless checks | Discussion | Companion Figure S4 and development evidence |
| Packet/slot/completion overhead | Sections 3 and 5.1 | Companion Table S3 |

Four main figures and three main tables remain. Compact header, placement, runtime, secondary-score and overhead details replace dependencies on the companion. Related-work and discussion repetition was shortened, without changing attribution or material limitations. Internal rights-review instructions were removed from the scientific narrative and retained in AUTHOR_REVIEW.

## Figure provenance

[build_submission_figures.py](build_submission_figures.py) produces manuscript-only PDF/SVG/PNG variants from retained artifacts. Figure 1 uses the original first manifest-ordered fixed cases and verbatim 249-byte excerpt. It states the complete carrier size, 616 tokens and 2,827 UTF-8 bytes, without an unavailable-file claim.

Figure 2 retains BSDS case **2018**, the previously used first held-out example. Original and stego images have equal display scale. The third panel is **32 × absolute RGB pixel difference**, an analytical visualization. The complete source/recovered 63-byte message remains visible. Source/carrier pixels are neither beautified nor changed. [Figure provenance](data/figure_variants.json) records source/output hashes, implementation identity and plotting versions. All accepted publication exports and carriers are unchanged.

## Reproduce and verify

From the repository root, using the existing analysis environment or equivalent installed NumPy, Pillow, Matplotlib and SciPy dependencies:

```sh
../llm-rankcloak/.venv/bin/python -B paper/icaart2027/build_submission_figures.py
python -B paper/icaart2027/build.py
../llm-rankcloak/.venv/bin/python -B paper/icaart2027/verify_consolidation.py
../llm-rankcloak/.venv/bin/python -B paper/icaart2027/verify.py
../llm-rankcloak/.venv/bin/python -B scripts/analyze_cover_rank_v1.py --verify-only
python -B paper/icaart2027/package_source.py
```

The interpreter path is an existing local environment, not an implicit sibling import. The compilation ZIP builds just the main with `python -B build.py --target main`, or both PDFs with `python -B build.py` and the standard TeX packages listed in [BUILD_README.md](BUILD_README.md). It includes the single-file main, separate companion sources and bibliography, required figures, notices and the unchanged official template. It excludes private keys, packets, model weights, contexts, environments, ledgers and build caches. Both PDFs compile in isolation and reproduce local extracted text.

Verification checks saved evidence and exact exported measurements, not new inference or private-key replay. It revalidates V1 qualification, V2, the GPU benchmark, context detection and the photograph study. All six current local ledgers are hash-unchanged. Do not run older analysis/export generators as a manuscript reset; accepted review packets are preserved.

## Compliance and remaining decisions

The current [ICAART Guidelines](https://icaart.scitevents.org/Guidelines.aspx) require 10,000–50,000 non-whitespace characters including references and graphics. The estimate counts extracted main text, counts the four figures' 1,635 text characters a second time, and adds 1,000 for extraction uncertainty. The margin is **5,865 characters**. This is not a portal-certified count. All visible figure text was inspected. No font, margin, line spacing or template change was used.

The official archive was retrieved again on 12 September 2026; its six retained files match the original template hashes. Both PDFs have empty author metadata. Ordinary third-person citations to prior work remain. [Policy/source record](data/single_pdf_policy.json) and AUTHOR_REVIEW separate completed editorial work from unresolved photograph republication, anonymous AI-disclosure placement and eligibility of the already-public manuscript history. The main is technically complete but not declared unconditionally submission-ready. No paper was submitted and no organizer contacted.

## Preservation and accounting

The earlier editorial finalization started at `79fd48c8b531f1eaeea28f2fc45457beac51b3ef`, with a clean tree and matching remote. Accepted artifacts, plans, configurations, application code and source manifests remain unchanged. The original manuscript asset copies and prior editorial records remain available alongside the new variants.

Cumulative historical use remains **89,404.217194 charged seconds**. This source consolidation adds **zero GPU seconds** and no new experimental observations. Commit/push is authorized for these editorial changes only; venue submission is not performed.
