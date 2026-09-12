# Author review of the ICAART 2027 draft

Anonymous Regular Paper, Area 2 Artificial Intelligence. No authorship, affiliation, funding, conflict declaration, permission or ethics approval has been invented.

## Contribution and novelty assessment

We develop a shared authenticated artifact-transport protocol with a controlled bidirectional comparison, and introduce reproducible model-rank embedding within an invariant coarse photograph. The latter retains bounded distortion and exact recovery without the receiver knowing the cover. The contribution distinguishes rank-map reproducibility from visual fidelity or security advantages that were not demonstrated.

| Claim | Evidence | Novelty boundary |
|---|---|---|
| Exact bidirectional saved-artifact transport | Figure 1, Table 2, Figure 3; fixed/gated 20/20 each direction and A1 PNG 20/20 | Calgacus proposes cross-domain rank transfer and Pixel-Stega already uses autoregressive image steganography. The shared authenticated recovery contract and matched empirical integration are the contribution. |
| Serialization-aware comparison | Main Method/Discussion; companion Figure S4, 40/40 sequence versus 22/40 static | RankCloak bounded-byte/gated coding and published stepwise verification are attributed, not claimed as inventions. |
| Arithmetic text capacity limitation | Section 5.2, 0/20 and observed information prefixes | A1 is a framing adaptation, not a bit-exact reference reproduction or impossibility result. Its separate finite-precision stagnation limitation remains distinct. |
| Known-model PNG detection changes with one row mismatch | Main Figure 4, paired fixed primary AUC change −0.1875 | Same 80 PNGs and twenty groups, not new transmissions, a blind observer or an isolated causal mechanism. |
| GPU execution improvement | Main Section 5.5, companion Figure S6/Table S6, 5.133075499× over nine fixed matched pairs | Standard CUDA graph infrastructure, three development payloads, pinned hardware and fresh-process boundary. Original V2 timings are not replaced. |
| Photograph-preserving model-rank transport | Figure 2, Table 3, Sections 3.5/5.6; 20/20 held-out per arm, exact rank digests and coarse invariance | New construction connects model ranks to invariant-context cells. QIM, nearest-distortion embedding and learned watermarking precede it. Invisible hiding itself is not new. |
| Learned partitions are distinct from simple parity | All 46,720 selected held-out partitions differ up to label swap; mean disagreement 0.44844 | Distinction does **not** establish benefit. Parity matches recovery and has slightly higher PSNR/SSIM and lower runtime. No superior security or trained-steganalysis result. |

Primary sources and exact versions are documented in [reference_verification.md](reference_verification.md). The original papers/software remain cited in third person. New references cover QIM, syndrome-trellis distortion minimization, HiDDeN, StegaStamp and BSDS500. These are conceptual comparisons, not unrun matched baselines. No universal-first or state-of-the-art claim is made.

## Current manuscript and evidence

This operation starts at `e39c14cc858bb67f870916692384d0e97502aa63` and adds the authorized 26-group photograph experiment. Its frozen execution identities, 52 original outcomes, six development checks and measured costs are separate from historical evidence.

The main remains 12 pages, with 42,189 extracted and 44,842 conservatively estimated characters, and a 184-word abstract. The companion is 11 pages. Figure 1A–B on page 4 preserves the actual historical image-to-text and generated-PNG examples. Figure 2 on page 6 contains the complete new photograph transport. Table 3 reports the two photograph arms. The detailed GPU plot moves to the companion, retaining its quantitative result and limitations in the main text. Header and mixture bookkeeping is consolidated in the companion; essential protocol remains in the main.

All six historical outcomes, accepted AUCs/intervals, measured GPU benchmark values and old artifacts remain unchanged. The new paper states the simple baseline's better mean fidelity and runtime directly. PSNR/SSIM and visual inspection are not interpreted as undetectability.

## Decisions before submission

1. **Authorship, originality and overlap.** Supply the actual author list in the appropriate venue fields. Confirm simultaneous-submission and prior-overlap obligations. Recalculate the template's self-reference proportion for the final actual authors and reference list. No identity is invented or concealed by omitting relevant prior work.
2. **Photograph permissions.** BSDS500 attribution is included, but the BIDS mirror does not establish blanket photograph republication permission. Confirm rights for the retained cover/stego/difference examples before upload or public dissemination. The images are local research/review derivatives, not project-owned or MIT-relicensed. Model weights are not included.
3. **AI disclosure placement.** [Guidelines](https://icaart.scitevents.org/Guidelines.aspx) require disclosure in acknowledgements and section-level tool citations but also omit acknowledgements for anonymous review. The [AI Tools page](https://icaart.scitevents.org/AiTools.aspx) permits an appropriate alternative section. The draft retains an anonymous AI ASSISTANCE DISCLOSURE and section-level citations. Confirm this resolution with the venue.
4. **Supplement status.** Separate supplementary upload for Regular Papers remains unverified. Prepare the companion for local review unless the chairs or submission interface confirm a route. The main includes essential methods, data, outcomes and limitations within its own limits.
5. **Anonymity and public history.** PDFs have empty author metadata and no affiliations, acknowledgements or project-repository link. Cited prior works and the distinctive public protocol can still permit identity inference. Review the existing project's relation to the venue's public-posting restriction; no historical artifact was hidden or rewritten.
6. **Other dissemination terms.** The PixelCNN++ port retains a sale restriction, and checkpoint redistribution permission was not established. The source ZIP contains no weights. Fashion-MNIST attribution and Gutenberg jurisdictional terms remain. Supply truthful funding, contributions, conflicts and data-sharing declarations if required.

## Ready-to-use AI disclosure

OpenAI Codex assisted with implementation, analysis scripts, figure preparation, and drafting and editing throughout this paper and its companion. Reported measurements come from retained execution records. Statistical plots display those measurements, and carrier examples are saved experimental artifacts, not AI-generated replacements. Tool assistance does not constitute independent scientific verification. Responsibility for factual accuracy, attribution and the final submission rests with the authors.

The exact assistant model identity for all historical sessions is not established. The Codex citation identifies the tool, not scientific evidence or an invented model version.

## Verification scope

The focused manuscript verifier rechecks historical public evidence, exact numerical claims, template/asset hashes, metadata and length. The new public analysis independently recomputes saved-image metrics and checks exported values, source equality, statuses and coverage. Private integration additionally checks old files, actual budgets and secret exclusion. These CPU checks are distinct from the new fresh-process GPU experiments, which are recorded in the extension's jobs and ledger.

All final main and companion pages are rendered and inspected. The source ZIP is compiled in isolation and reproduces both PDF texts. Total new experiment charge is 429.149258 seconds. Manuscript compilation/inspection adds zero. See [verification.json](verification.json), [visual_inspection.md](visual_inspection.md), [source archive verification](source_archive_verification.json) and the [extension review](../../artifacts/cover_rank_v1_review/README.md).
