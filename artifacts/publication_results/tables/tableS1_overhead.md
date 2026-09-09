# Framing, padding and carrier-position overhead

| Carrier / method | Slot pad (B) | Packet-positive positions | Skipped positions | Zero-bit positions | Completion positions | Packet bits / span symbol | Suffix bits |
|---|---|---|---|---|---|---|---|
| UTF-8 / Fixed | 0.0 | 584.00 | 0.00 | 0.00 | 32.00 | 4.000 | 0.0 |
| UTF-8 / Gated | 0.0 | 584.00 | 39.80 | 0.00 | 32.00 | 3.747 | 0.0 |
| UTF-8 / A1 | 0.0 | 399.40 | 0.00 | 1648.60 | 0.00 | — | 0.0 |
| PNG / Fixed | 162.8 | 584.00 | 0.00 | 0.00 | 2392.00 | 4.000 | 0.0 |
| PNG / Gated | 162.8 | 584.00 | 100.50 | 0.00 | 2291.50 | 3.451 | 0.0 |
| PNG / A1 | 162.8 | 508.20 | 0.00 | 89.65 | 2378.15 | 3.934 | 28.9 |

Descriptive cell means over 20 held-out attempts. Every packet is 292 B: 36 B framing/encryption plus the 256 B payload slot. Rank alignment adds zero padding bits. The four position columns partition delivered symbols: packet-positive + skipped + zero-bit + completion. A1’s one successful termination position is already among packet-positive positions, never another position to add. Packet-span transport is 2,336 / packet stopping position (including skips/zero-bit steps), undefined for unfinished A1 text. Whole-carrier packet rates and file expansion are in the CSV. A1 PNG suffix bits (mean 28.9) are discarded zero-extension emissions, not useful packet bits; lookahead zeros (mean 29.9, CSV) overlap that diagnostic and must not be summed with it. A1 text reaches neither suffix processing nor completion.
