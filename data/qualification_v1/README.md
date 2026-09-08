# Frozen CPU source/context preparation, V1.2

No held-out carrier has been generated. Selection uses source bytes, class labels
and fixed rules only, never carrier outcomes.

Reproduce with the pinned V0 control/image interpreter (NumPy 2.2.6, Pillow
12.3.0):

```sh
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/prepare_v1_sources.py --output /tmp/imagecalgacus-source-reproduction-NEW
```

The output must not exist. The default ignored cache is
`.runtime/source_cache`. A missing cache is downloaded from the frozen URLs,
then checked against `configs/v1_sources.json`; changed upstream editions fail,
not silently replace the corpus. Archive hashes identify exact versions.
The initial acquisition used `--acquire`; subsequent preparations do not need
it. Frozen payloads, contexts, manifest and terms reproduced byte-for-byte in
`.runtime/v1_2/source-reproduction`. This README is explanatory, not generated
by the preparation command.

## Sources and deterministic selection

There are 20 images and 20 texts in each split. I1–I5 and T1–T5 are byte-preserved
accepted fixtures. Added development image labels are 0–9 followed by 0–4;
each chooses the smallest unused Fashion-MNIST training IDX index of that class
after original/canonical duplicate rejection. Held-out labels are 0–9 twice,
using test IDX data, hence two per class. Images remain unsigned 8-bit grayscale;
Pillow BOX resizes 28×28 to 16×16 without inversion or normalization.
Each canonical image is exactly 256 bytes. PNG metadata is not a payload.

Development texts alternate Gutenberg 11/84; held-out texts alternate 1342/1661.
The added development allocation is seven 32–64-byte and eight 65–128-byte spans,
making ten per band with the original fixtures. Held-out has ten per band.
Fixed first-narrative anchors exclude titles, tables, credits and the Austen
editorial preface. Source-specific anchors and byte bounds are recorded for
every excerpt. Eligible paragraphs have at least 128 bytes, 20 ASCII words and
60% lowercase ASCII letters; paragraphs containing Gutenberg, contents,
illustration, transcriber or copyright are excluded. Select the first unused
eligible paragraph, start at its first ASCII word and take the longest
whole-word, valid UTF-8 ending in the specified band. No normalization, newline
conversion or paraphrasing occurs. Byte offsets refer to the original downloaded
UTF-8 files (including any BOM/header/CRLF bytes). Selected spans do not overlap.
The manifest exclusion array records duplicate-candidate exclusions (zero here);
front-matter and paragraph eligibility exclusions are defined above and in code,
not claimed to be zero.

Original/canonical image hashes and canonical payload hashes are unique across
the selected splits. Original IDX train/test namespaces and disjoint book IDs
prevent original-source overlap. Exact original offsets/indices, labels,
preprocessing, file and payload hashes are in `manifest.json`.

Fashion-MNIST revision `b2617bb6d3ffa2e429640350f613e3291e10b141` includes
Zalando's MIT notice in [terms/FASHION_LICENSE.txt](terms/FASHION_LICENSE.txt).
Books acknowledge Lewis Carroll (11), Mary Wollstonecraft Shelley (84),
Jane Austen (1342) and Arthur Conan Doyle (1661). Download URLs, edition headers,
file hashes and Project Gutenberg provenance are retained; see
[terms/GUTENBERG_LICENSE.txt](terms/GUTENBERG_LICENSE.txt) and the repository
[attribution](../../THIRD_PARTY.md). These narrative works are unrestricted under
US copyright; redistribution elsewhere requires checking local terms.

## Contexts and randomness

Prompt1 and row1 are unchanged accepted V0 bytes. Prompt2 is exactly:

> Explain how a home cook prepares a simple vegetable soup. Use continuous prose.

There is no trailing newline. Row2 is a payload-independent 96-byte RGB row:
NumPy `Generator(PCG64(2002)).integers(0,256,96,dtype=uint8)`.
It is not selected for appearance and has no model inference cost.
Context hashes are in the manifest. These deterministic preparation/ordinary
sampling seeds are never cryptographic keys or nonces.

`configs/v1_qualification.json` supplies work identities and legacy credits.
`configs/v1_2_batch.json` freezes the six authorized first-batch cases and
per-process bounds. Held-out sources are deliberately absent from every
qualification work record and from this batch.
