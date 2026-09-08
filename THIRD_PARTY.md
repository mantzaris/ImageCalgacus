# Attribution and acquisition

## RankCloak

Adapted from mantzaris/llm-rankcloak at
[ce853d42d6ba64065cb63c6bdfc0d825c62734cd](https://github.com/mantzaris/llm-rankcloak/tree/ce853d42d6ba64065cb63c6bdfc0d825c62734cd):

- rank_codec.py: stable descending-logit/ascending-ID ordering, bounded byte/rank bridge and incremental generation/replay pattern. Adapted in fixed_rank.py and sender/receiver loops; strict fixed-size parsing replaces sender metadata.
- model_io.py: CUDA library preloading, explicit offload capability, batch/microbatch 1, numerical environment controls, full context/KV reset, context-once incremental evaluation and exact-byte detokenization. Adapted in text_backend.py/runtime.py. CPU defaults and display replacement decoding are not reused.
- token_filters.py/revision_protocol.py: matched filtering/replay patterns. The main filter uses complete-prefix verification, not the isolated-token/prose mask or source-bearing Representation.

These adaptations retain the MIT notice in LICENSE (Copyright 2026 a.v.mantzaris). There are no imports of RankCloak application code or its research pipeline. Local interpreter/model paths are explicit configuration.

[Calgacus](https://arxiv.org/abs/2510.20075), RankCloak's bounded-byte coding, and [stepwise tokenization verification](https://aclanthology.org/2025.emnlp-main.361/) are prior work, not new inventions here.

## PixelCNN++

Inference-only model/layers/helpers are adapted from
[pclucas14/pixel-cnn-pp, 7cb4436f062fda9b63ecc9e3b75d2c2dcb379931](https://github.com/pclucas14/pixel-cnn-pp/tree/7cb4436f062fda9b63ecc9e3b75d2c2dcb379931).
The port's nonstandard, sale-restricting notice is preserved verbatim in imagecalgacus/pixelcnn/LICENSE; those portions are not relicensed under the root MIT license.
Original OpenAI notices are preserved in imagecalgacus/pixelcnn/OPENAI_LICENSE.md.
Original implementation revision: bbc15688dd37934a12c2759cf2b34975e15901d9.

Changes: relative imports and an inference-only helper subset, input-device/dtype padding per forward, removal of debug/training paths. The author's uniform DataParallel module. checkpoint prefix is removed bijectively; every resulting tensor must strictly match. No parameter conversion or model training occurs.

The logistic-mixture parameterization is reused; new float64 discrete-CDF code implements the approved exact RGB conditionals and mixture posterior updates. The original continuous sampler and density fallback are not used. [PixelCNN++ paper](https://arxiv.org/abs/1701.05517).

The checkpoint was acquired from the author's README-linked public MEGA folder, file handle C7gDHIIB, name pcnn_lr.0.00040_nr-resnet5_nr-filters160_889.pth, 214,732,802 bytes. Local SHA-256: a5ed558f6d4098ce3cbfd47658b7e3be37fae77b71a90c8a56f46a6266ff833f. Acquisition has TLS, exact-size and local-hash checks, not an author-published checksum. No separate checkpoint notice was observed; use is limited to this local research evaluation under the repository's non-sale terms. Weights are not distributed in this repository/review packet.

## Text weights and dependencies

Existing QuantFactory Llama 3 8B Instruct Q4_K_M GGUF at revision a06c33ec89c1e3402009fb47f466a89127c6d223; content SHA-256 verified as 86c8ea6c8b755687d0b723176fcd0b2411ef80533d23e2a5030f845d13ab2db7. The GGUF identifies its license as llama3; Meta Llama 3 Community License and Acceptable Use Policy apply separately from code licenses. Model weights are not redistributed. Dependency distributions retain their original notices.

The V0 source fixtures are synthetic images and newly authored text, not external datasets.
