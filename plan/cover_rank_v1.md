# cover_rank_v1 protocol and bounded evaluation

This is a separately authorized photograph-preserving extension, not a revision of the accepted generated-image or text protocols. Starting source revision is e39c14cc858bb67f870916692384d0e97502aa63. Accepted carriers, failures, ledgers and analyses are preserved. No text-model inference or implementation change is involved.

## Reuse and difference

Reuse ImageBackend.forward and its CUDA graph capture/replay, strict checkpoint loading, float32 normalization, GPU allocation checks and deterministic settings. Reuse RGBConditionals parameter layout and exact discretized logistic bin definition, packet.Payload/open_packet/NewRun, strict RGB PNG I/O, and the existing serial occupied-process accounting wrapper. The new joint log-score routine preserves candidate-dependent green and blue means and common mixture weights. It is checked against the independently sequenced existing channel implementation.

The local RankCloak checkout was inspected at ce853d42d6ba64065cb63c6bdfc0d825c62734cd, including README NVIDIA setup, model_io.load_llama_cpp_model and CUDA numerical controls. Its environment and previously adapted replay precautions remain in use. No sibling source imports or whole-pipeline copy are introduced. Its llama.cpp CPU-default loader is not invoked. PixelCNN++ remains a pixel autoregressive model, not an LLM. Existing third-party licensing and attribution remain applicable.

## Wire and rank contract

The delivered image is 256×256 RGB8 PNG. Let B(c)=4 floor(c/4). For every channel its output remains B(c)..B(c)+3. The network input is B+2. Partition it into 64 nonoverlapping 32×32 tiles in row-major order. Exactly one forward pass per tile supplies every pixel parameter vector. Graph setup includes the existing three warmup forwards and capture. No autoregressive candidate-generation loop is introduced. Each process releases the backend on exit.

At each selected pixel, enumerate all 64 candidates in lexicographic RGB order. For each candidate evaluate log sum_k w_k f_k(r) f_k(g|r) f_k(b|r,g), with discretized logistic bins, edge tails, clipped log scales at -7, and tanh coefficients exactly as the existing implementation. Green uses the candidate red; blue uses candidate red and green. Float64 logaddexp operations retain all64 finite scores without converting to normalized probabilities or excluding underflowed probabilities. Nonfinite values cause an explicit failure.

Sort by descending log probability, ties by lexicographic RGB. Zero-based rank modulo two is the bit. Both partitions contain32 candidates. Select the candidate of minimum squared RGB distance to the original pixel within the required partition, ties lexicographically. The receiver reads observed rank parity. The ordinary parity comparator instead labels each candidate (r+g+b) mod2, retaining identical selection, positions, packet and distance rule.

These model scores define a fixed coarse-context embedding rank map. They are not V2 likelihoods conditioned on the actual full-precision delivered history, nor evidence of distribution-preserving sampling.

## Packet, placement and secrecy boundaries

The existing packet remains292 bytes: 12-byte random nonce, AES-256-GCM ciphertext of the264-byte plaintext, and16-byte tag. Plaintext is the existing eight-byte big-endian version/type/length/dimensions header and256-byte zero-padded slot. Text is literal strict UTF-8,32..128 bytes, zero dimensions. AAD remains ImageCalgacus/packet/v1. No new MIME, padding or compression.

Serialize all2,336 packet bits most-significant bit first. Derive a32-byte placement key by HKDF-SHA256 from the run key, salt SHA256(coarse RGB bytes), and domain-separated info containing the canonical protocol hash. For each raster pixel index compute HMAC-SHA256(placement_key, domain || uint32be index). Sort by digest, then index; the first2,336 distinct indices give bit placement and ordering. This is independent of the hidden nonce. The arm is deliberately absent from placement derivation.

Prepare one fresh encryption per cover/text group, with a newly generated run key and independently random unique nonces checked within the run. Both arms reuse that immutable sealed packet. Continuation only uses retained, verified packet bindings; it never performs a second encryption under an old run key.

Receiver inputs are the delivered PNG, agreed profile/arm and cryptographic key. Coarse context is reconstructed from that PNG. A fresh receiver process reads a restricted three-file input directory containing carrier.png, profile.json and run.key. It never reads the original cover, source text, prepared packet, evaluator manifest, saved rank map or sender diagnostics. The evaluator compares source bytes only after receiver exit. Public review directories are not receiver inputs.

Correctness follows from cell invariance: both endpoints reconstruct identical tiles and keyed positions. Identical parameter/log-score/order streams imply identical balanced labels; observed label recovers every bit. Strict authenticated parsing then recovers the source. This is conditional on the pinned deterministic numerical implementation, tested across fresh processes, not a cross-hardware guarantee. Authentication protects the packet, not every cover pixel. Unused low-bit changes can leave the packet intact.

## Frozen data and allocation

Use the BIDS BSDS500 mirror at a04b7c6c3a9f0ace74bf205c72a43d32e1c72722, the January2013 distribution. Select the six smallest numeric training-image filenames and twenty smallest numeric test-image filenames. Convert to RGB and center-crop256×256 with floor offsets, without resizing. Source bytes, crop boxes, original partition, URLs, hashes and final pixels are recorded before outcomes. No substitutions or outcome-dependent selection are allowed.

Pair development images in order with retained T1..T6 and evaluation images with HT1..HT20 from the existing source manifest. Text provenance and original bytes are preserved. All26 pairings are frozen before embedding. Development is12 carriers, held-out evaluation40, total52. Within each group execute model arm then parity, each sender followed by a fresh receiver. Timing repetitions are not allocated.

Dataset attribution is Arbeláez, Maire, Fowlkes and Malik, Contour Detection and Hierarchical Image Segmentation, TPAMI2011. The mirror README requests this citation. No blanket image redistribution license was found in the inspected distribution. Photographs are not covered by the project code license. These are local research/review derivatives; publication reuse permission remains an author check.

## Gates, measurements and budget

Before any held-out embedding, require all12 development source recoveries, exact fresh-process parameter/log-score/rank digests, invariant and bound checks, and positive process-specific GPU evidence. A three-tile first-development-cover probe compares reference and graph parameter maps exactly and checks joint scores against sequential channel conditionals. CPU synthetic checks cover extreme underflow, ties, candidate dependencies, key placement, authentication failure, unused-pixel behavior and allowance idempotency.

For both arms of the first development group, perform one wrong-key receiver, one deliberately flipped embedded-bit receiver and one compression9 PNG re-save receiver. The first two must reject authentication without producing plaintext. Re-save must preserve RGB bytes and recover. These six receiver checks are not extra scientific carriers. Corrupted and re-saved copies remain private diagnostic artifacts. They are not replacements.

The new absolute allowance is7,200 seconds, applied once, with the144,000-second cumulative cap also enforced. At inspection historical usage was88,975.067936 seconds. Every model job is charged from process launch through exit, including imports, model hashing, loading, warmup, CPU rank work, serialization and teardown. Model-free baseline child times are conservatively charged to this allowance as well, reported separately rather than described as GPU inference. Hard limits are120 seconds for the probe,90 per model process and20 per baseline process. Reserve220 seconds before starting a complete group. After development, project remaining work using at least30 seconds per model process and5 per baseline process, or1.5 times the respective largest measured duration, whichever is larger, plus120 seconds headroom. Stop on budget, GPU, invariant or recovery discrepancies. Preserve failures; do not tune held-out cases.

Report PSNR from pooled RGB MSE with peak255. SSIM is the mean channel-wise score using Gaussian sigma1.5,11×11 support, valid centers, population covariance, K1=.01,K2=.03 and data range255. Report changed-pixel/channel fractions, max channel difference, file bytes, packet rate2336/65536 bits/pixel, useful source bytes, fresh-process and nested phase times. Descriptive paired means/ranges retain every case. No detection inference or significance testing is added.

Independently, SSE ≤2336×3×9, hence MSE ≤9×2336/65536 and PSNR ≥53.0685 dB. This conservative bound is not a measured score. Compare learned versus parity partitions allowing label swap using min(Hamming(L,C),64-Hamming(L,C))/64 at every selected pixel. Report the fraction differing and average distance. Different images alone do not establish distinct partitions or an advantage.

Select the first three held-out identifiers for cover/stego/32×absolute-difference panels, and the first held-out source/carrier/recovered text for the complete example. No image enhancement is permitted. New manuscript figures and tables derive only from these retained results. Visual fidelity is not steganalytic security or JPEG robustness.
