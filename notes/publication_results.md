# Publication figures and tables

Completed the bounded reporting package at [artifacts/publication_results/README.md](../artifacts/publication_results/README.md): four main figures, four main tables, two supplementary figures and one supplementary overhead table. All requested figures were supported by retained evidence. No model inference, GPU experiment, source generation, statistical refitting or manuscript drafting occurred.

## Starting point and scope

The checkout began clean at `5e08a8ba32136c0ec51e8d27b355e83ca956786a`, the reviewed GPU benchmark revision, with no subsequent commits. Applicable repository/ancestor instruction checks found no AGENTS.md. Both plans, accepted V2 and benchmark notes/review packets, the V1 qualification comparison, frozen manifests, analysis definitions, arithmetic audits and timing records were inspected.

Only the new reporting entry point, this note and `artifacts/publication_results/` were added. Historical model execution identities are preserved separately in [historical_execution_identities.json](../artifacts/publication_results/data/historical_execution_identities.json); no historical experiment is attributed to the new plotting script. Application, protocol, tests, plans, existing result files and ledgers were not modified.

## Outputs and interpretation

- Figure 1 uses HI1/prompt1/fixed and HT1/row1/fixed, selected directly as the first manifest-ordered fixed examples. The source/recovered images show the actual 16×16 grayscale pixels; the delivered PNG is the actual 32×31 RGB8 carrier. Images use nearest-neighbor enlargement and correct aspect ratios. The carrier excerpt is a literal leading byte range, with display wrapping only and links to the full file. The text payload is all 63 original UTF-8 bytes. Exactness is canonical raw pixels/literal text, not arbitrary original image containers.
- Figure 2 and Table 2 retain all six V2 cells: text fixed/gated 20/20, text A1 0/20, and PNG fixed/gated/A1 20/20 each. Failed or unauthenticated delivery has zero exact goodput. Text-token and PNG-channel units are separate. Original V2 timings, not graph timings, populate Table 2.
- Figure 3 and Table 3 retain the frozen higher-is-stego score direction, all 20 failed A1 text carriers, and the accepted grouped intervals. Both mean-surprisal and mean-log2-rank scores appear in the table. Four-decimal AUC displays avoid ambiguous three-decimal half-way rounding of values such as 0.5575 and 0.5025; full-precision values remain in CSV. Perfect empirical text separation does not establish perfect population detection, and near-chance AUC does not establish security.
- Figure 4 emphasizes the nine fixed-rank timing comparisons (three repetitions on each of T1/T4/T5). The accepted pooled charged-time speedup is 5.133075499074237×; recovered-source throughput is 0.47988972747811365 → 2.4633102023753177 B/s. Table 4 additionally includes the one-payload gated/A1 measurements. All 11 comparisons/22 recoveries retain exact stream/carrier/source equivalence. PyTorch allocated, reserved and sampled process memory remain distinct. CUDA-event intervals are nested measurements, never additional charges. These are development engineering timings, not new V2 observations.
- Figure S1 uses all 40 V2 arithmetic audits, with actual checkpoints every 128 positions plus recorded endpoints. No intermediate observations were invented. Packet-prefix bits are capped at 2,336 before suffix diagnostics; PNG curves end at packet stop rather than extending through ordinary completion. Text endpoints are 581–2,216 bits. Isolated unchanged intervals remain transient effects, not a relabeling of the accepted low-information diagnosis as sustained stagnation.
- Figure S2 preserves I1–I20 identities across both development prompts: sequence 20/20 under each; static 8/20 and 14/20. The 40 context-specific pairs are only 20 distinct payloads. The unavailable historical static matched-control prefix is neither regenerated nor assigned a score.

Table 1 gives the frozen experimental specification and abbreviated checkpoint identities. Table S1 keeps framing, slot padding, skips, zero-bit positions and completion separate; the A1 termination position is a subset of packet-positive positions. Lookahead and discarded-suffix counts are overlapping diagnostics, not additive bits.

## Numerical and visual verification

The generation command completed successfully using the existing Python 3.10.13 / NumPy 2.2.6 / Pillow 12.3.0 / Matplotlib 3.10.9 environment, plus installed LaTeX and Poppler. No dependencies were installed.

```sh
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/build_publication_results.py
```

The script reads accepted intervals without rerunning bootstrap analysis. Focused assertions cross-check raw result counts, boundary recovery intervals, cell means, exact-goodput denominators, AUC point estimates, shared-control identities, original paired packet digests, position-accounting identities, saved cross-mode carrier/source equality and recorded exact probability-stream hashes. New filtering fractions and endpoint/memory displays are descriptive summaries of existing records only. Supporting [verification.json](../artifacts/publication_results/data/verification.json) records these checks; test counts are not paper results. No unit-test suite or CPU portability campaign was started.

The three public saved-evidence verifiers also passed, without private authentication or neural replay:

```sh
python -B scripts/collect_v2_review.py --verify-public artifacts/v2_review
python -B scripts/collect_gpu_performance.py --verify-public
python -B scripts/finalize_v1_qualification.py --verify-public artifacts/v1_qualification_review
```

They reconcile V2's 120 outcomes/40 controls, the benchmark's 11 comparisons/22 recoveries and V1's 152 outcomes. Their exact responses are saved in [public_evidence_verification.json](../artifacts/publication_results/data/public_evidence_verification.json).

Every figure was visually inspected from its rendered PNG. Every table was compiled from its actual manuscript LaTeX and its resulting PDF preview inspected; all five compile to one page without overfull boxes. The example footer spacing and one overlong panel title were corrected. Final AUC labels, abbreviated checkpoint identities and arithmetic target placement were re-inspected. Axes, units, point/legend styles, source pixels, paired IDs and non-clipping were checked. Tables were also read in Markdown, with full numerical precision retained in CSV. PDFs/SVGs keep chart/text geometry vector-based; the real image panels necessarily embed raster pixels. Every figure also has a 450-dpi PNG.

Source paths/hashes, the accepted statistical-content hash, reporting-script hash, generation environment, figure/table captions and claim-to-evidence limitations are in the new package. A reporting bounds guard initially mistook an undrawn automatic tick outside the axis range for visible text; the guard was corrected to check only drawn ticks. An added cross-mode verification used the wrong record-ID field on its first CPU attempt and was corrected to the actual frozen `case.id`. Neither issue touched experimental data or model code.

## Preservation and accounting

The build verifies 3,544 protected public evidence, configuration, source/context, protocol and ledger files byte-for-byte before/after. Both aggregate preservation digests are `cc8b4b687cfe0599ff3032f5951ccd58e405dc1a94f478986b97ae6ccbbae816`. All accepted V2 and GPU benchmark artifacts/analyses remain unchanged. Private keys, prepared packets, model weights, private environments and raw private diagnostic traces were not read or exported; original public digest references remain provenance, not receiver inputs.

New charged GPU time is **0 seconds**. Read-only local ledger reconciliation agrees with accepted history: V0 3,163.653124010041 s; V1 39,995.5091691459 s; V2 42,024.52764170886 s; GPU benchmark 2,351.732528250024 s. Cumulative use remains **87,535.42246311482 seconds**, leaving 56,464.577536885176 seconds below the whole-project ceiling. No allowance was changed and no GPU job was launched.

This completes publication-result presentation, not journal acceptance or a full manuscript. No experiments, commit, push or publication followed.
