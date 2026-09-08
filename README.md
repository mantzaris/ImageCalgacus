# ImageCalgacus: V0 and bounded V1 development

Transport of canonical 16×16 grayscale images through generated UTF-8 text, and 32–128-byte UTF-8 messages through generated RGB PNGs. Accepted V0 uses fixed radix 16; the bounded V1 pilot adds entropy gating and arithmetic coding, with documented arithmetic text capacity failures. Both neural backends use the selected local NVIDIA GPU. The receiver reads actual artifacts, not sender token IDs or latent codes.

See [the approved implementation plan](plan/implementation_plan.md), [attribution](THIRD_PARTY.md), and [V0 results](notes/v0_results.md). This is a small functionality demonstration, not a security, imperceptibility or journal-study result.

## Environment

The checked-in configs/v0.json records this host's explicitly selected GPU UUID, model hashes, interpreter paths and full-offload text profile. Those paths are configuration, not imports of sibling application code. Another host must select and preflight its actual suitable GPU and compatible CUDA builds; no CPU/partial-offload fallback exists.

Verified local runtimes:

- Text: RankCloak's .venv-generation-v3 interpreter, llama-cpp-python 0.3.23 CUDA build, NVIDIA runtime 12.4.127 and cuBLAS 12.4.5.8.
- Image: RankCloak's .venv interpreter, PyTorch 2.5.1+cu124.
- NumPy 2.2.6, cryptography 46.0.7, Pillow 12.3.0. The missing text-environment Pillow package is installed only into the project's ignored .deps-text directory.

No existing RankCloak environment was changed. For this environment the additional installation command was:

    /home/meow/Documents/repos/llm-rankcloak/.venv-generation-v3/bin/python -m pip install --no-deps --target .deps-text Pillow==12.3.0

Text weights are reused by explicit path/hash. The public author-linked pixel checkpoint was acquired with:

    /home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/acquire_pixel_checkpoint.py --output models/pixelcnn_pp_cifar10.pth

Do not rerun acquisition over an existing checkpoint. Read THIRD_PARTY.md before redistribution: the pixel port has nonstandard non-sale terms; neither model is included in version control.

## Budget and CPU tests

Every neural-model command must run through imagecalgacus.runtime (or the demo runner that calls it). The wrapper serializes jobs, conservatively charges complete process wall time including model loading/CPU filtering, and terminates at the remaining allowance. Never delete/reset its ledger to evade the approved 7,200-second limit.

    /home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.runtime --status
    /home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m unittest discover -s tests -v

CPU tests contain no neural inference. The runtime adds only this project and .deps-text to PYTHONPATH. CUDA graphs/fusion/workspace/precision controls, batch/microbatch 1, full context/KV reset and incremental evaluation are preserved.

## Commands used for V0

These commands require new output/run directories and available remaining budget; they do not resume encoding under an old key.

    /home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.runtime --label text-preflight-1 -- /home/meow/Documents/repos/llm-rankcloak/.venv-generation-v3/bin/python -B -m imagecalgacus.preflight --backend text --profile configs/v0.json --output .runtime/text-preflight-1
    /home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.runtime --label image-preflight-1 -- /home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.preflight --backend image --profile configs/v0.json --output .runtime/image-preflight-1
    /home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.demo --prepare
    cp .runtime/image-preflight-1/row.rgb artifacts/v0_review/contexts/row.rgb
    /home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.demo --mode preliminary --cases configs/v0_cases.json --profile configs/v0.json --new-run runs/preliminary-001
    /home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.demo --mode ten --pilot runs/preliminary-001 --cases configs/v0_cases.json --profile configs/v0.json --new-run runs/ten-001

The fixed fixtures are frozen by --prepare, not chosen from generated outputs. The shared row is the first row of the first ordinary image, seed 2001. A demonstration groups standalone case encoding runs; each gets a fresh OS-random key and unique random nonce. Keys remain in ignored, private runs directories. No sender packet/token/rank cache is saved or used by decoding.

## Standalone sender and receiver interfaces

For one image-to-text case, the demo invokes the following interfaces (use a new label and encoding directory for a new run):

    <text-python> -B -m imagecalgacus.sender image-to-text --source <source.png> --profile configs/v0.json --context <prompt.txt> --new-run <new-run>
    <text-python> -B -m imagecalgacus.receiver image-to-text --carrier <inbox/carrier.txt> --profile <inbox/profile.json> --context <inbox/prompt.txt> --key <inbox/run.key> --output <recovered.gray> --report <receiver.json>

For text-to-image:

    <image-python> -B -m imagecalgacus.sender text-to-image --source <source.txt> --profile configs/v0.json --context <row.rgb> --new-run <new-run>
    <image-python> -B -m imagecalgacus.receiver text-to-image --carrier <inbox/carrier.png> --profile <inbox/profile.json> --context <inbox/row.rgb> --key <inbox/run.key> --output <recovered.txt> --report <receiver.json>

Prefix each standalone model invocation with:

    <control-python> -B -m imagecalgacus.runtime --label <unique-label> --

The receiver input directory must contain exactly carrier, profile, context and key; output/report go elsewhere. It rejects extra inputs and imports neither sender, demo nor evaluator. The model file/runtime are declared assets. This is data-flow separation, not an OS sandbox. Existing environment controls are not disabled.

The evaluator runs as a separate CPU process:

    /home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B -m imagecalgacus.evaluate --run runs/ten-001 --references runs/ten-001/references.json

Final mode compares bytes against the frozen source, reconciles all expected work, and checks authentication and evidence without rewriting historical files. Explicit --mode progress writes subset results and recovered viewable grayscale PNGs. The transmitted image is width 32, height 31, RGB8; bits/pixel and bits/channel are different units. Text carriers contain 584 packet tokens and exactly 32 completion tokens.

## Review packet

After all work has stopped:

    /home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/collect_v0_review.py --run runs/ten-001 --preliminary runs/preliminary-001

The review collection contains public fixtures, both preliminary artifacts and all ten V0 artifacts/recovered outputs, compact results, GPU evidence summaries, tests and source hashes. Keys, weights, environments and full logs are excluded. Public review directories contain ground truth and must never be used directly as receiver input directories; stage only the four permitted inputs with a locally retained key.

## V1 development

V0 artifacts and historical results remain unchanged. V1 adds strict entropy gating, the independently written 32-bit arithmetic comparator with approved finite-stream framing A1, and a four-payload/three-method GPU pilot. See [V1 results](notes/v1_results.md) and [the review packet](artifacts/v1_review/README.md). Neither V1 full qualification nor V2 is implied by command success.

The optimized text path preserves top-256-before-filtering, exact eligible distributions/ranks, full-prefix tokenization, byte serialization and GPU replay settings. A matched-packet GPU harness compares the retained reference implementation against it. No candidate-limit, precision, model or backend change is used.

V1 has a separate 7,200-second ledger; V0's 3,163.653124 seconds are retained. The global GPU lock is shared, so jobs remain sequential. Use --stage v1 on the wrapper:

    <control-python> -B -m imagecalgacus.runtime --stage v1 --status
    <control-python> -B -m imagecalgacus.runtime --stage v1 --label <new-label> -- <model-command>

The configured interpreters are the same V0 environments above. Do not reset ledgers or run models outside the wrapper. The 40-hour study ceiling is not permission to spend beyond the currently authorized stage.

Executed V1 command identities, with exact local paths/arguments, are recorded in artifacts/v1_review/gpu_jobs.json. The main interfaces are:

    <control-python> -B scripts/calibrate_v1.py
    <control-python> -B -m imagecalgacus.v1_pilot --new-run <new-pilot-run> --packet-run <new-private-packet-run> --revision <starting-revision>
    <control-python> -B -m imagecalgacus.evaluate --run <run> --references <run/references.json> --mode progress
    <control-python> -B -m imagecalgacus.evaluate --run <run> --references <run/references.json> --allow-failures --output <new-validation.json>

Calibration and pilot preparation are deliberately single-use: frozen configurations, existing run directories and existing result summaries cannot be silently overwritten. A new scientific allocation is not authorized by these examples. See the results for any explicitly recorded continuation in a fresh key/run namespace.

The three profiles are configs/v1_fixed.json, configs/v1_gated.json and configs/v1_arithmetic.json. A sender may take --prepared-packet and --key together; the pilot privately encrypts each payload/context only once, and gives the same packet to all three senders. These arguments are NEVER receiver inputs. A receiver still gets only carrier, profile, context and key, in a directory containing exactly those four files.

Progress can report a subset. Final validation requires all expected IDs, valid evidence and terminal outcomes. By default its exit status additionally requires all recovered; --allow-failures permits a complete allocation with recorded failures. Always inspect allocation_complete, attempted_count, completed_count, exact_recovery_count and all_recovered. V0 retains strict 10/10 acceptance.

No full datasets, second-context qualification, static-mask matrix, detector studies, statistical inference or V2 runs are performed here. A1 zero-bit/quantization stagnation and exhaustion of either carrier budget are explicit failure outcomes, not opportunities to flush hidden bits, change thresholds, extend carriers or reroll packets.
