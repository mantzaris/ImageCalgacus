# Literal retained examples

These are the first manifest-ordered fixed-rank prospective cases in each
direction. They were not selected for appearance. The copies are byte-identical
to accepted V2 files, with SHA-256 identities in
[`data/asset_provenance.json`](../data/asset_provenance.json).

| Direction | Source | Delivered carrier | Recovery |
|---|---|---|---|
| Canonical image to text | [HI1 source PNG](HI1-prompt1-fixed/source.png), 16 × 16 grayscale, 256 canonical bytes | [Complete UTF-8](HI1-prompt1-fixed/carrier.txt), 616 tokens | [Raw pixels](HI1-prompt1-fixed/recovered.gray) and [viewable PNG](HI1-prompt1-fixed/recovered.png) |
| Text to PNG | [HT1 literal source](HT1-row1-fixed/source.txt), 63 UTF-8 bytes | [Delivered PNG](HT1-row1-fixed/carrier.png), 32 × 31 RGB | [Recovered text](HT1-row1-fixed/recovered.txt) |

The image equality endpoint is the canonical grayscale array, not the original
Fashion-MNIST container or an arbitrary original file. Text equality is literal
source-byte equality. See [source notices](../ASSET_NOTICES.md). No row bytes,
key, packet or sender trace is included here. These example files accompany
the local manuscript and are not part of the compilation-only source ZIP.
