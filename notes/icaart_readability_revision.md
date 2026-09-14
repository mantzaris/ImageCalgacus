# ICAART opening-passages readability revision

Starting Git revision: `6970fa43d02eda8862634c56325dd6f856b05010`.

The starting worktree already contained author edits to the abstract and introductory prose, removal of some origin comments and two drafting footnotes, and the earlier local-template dependency repair. These were retained as the manuscript basis. Untracked `paper/icaart2027/main.pdf` and `texput.log` were left untouched and excluded from the commit.

Starting working manuscript SHA256: `0f32b5bb73eb2521e5239c3d41b4dcec962cc94643d1aa6da825d02c8bedf0f0`.
Revised manuscript SHA256: `d01961727ba427bba1a34d57d38c0ed7f8ae96c7d1cb04b649f2438666029d21`.

## Scope and verification

Only the abstract, first Introduction paragraph and an added Method opening differ from the starting worktree. Replacing these three regions with placeholders produces identical remaining source. Existing section 3.1 and all subsequent formal text, equations, tables, figure captions, citations and the formatted bibliography are unchanged. The main remains one editable LaTeX file.

The abstract has 191 words. The Introduction defines payload and carrier through a concrete communication task. The Method overview precedes the unchanged detailed contract and separates receiver authentication from the evaluator's source comparison.

The established build and manuscript verification pass. The verifier now distinguishes historical consolidation equivalence from later authorized prose changes and checks actual preamble settings independently of removable origin comments. No statistical or experimental check was relaxed. It revalidated 3,700 protected public files, six original recovery cells, retained detection and benchmark numbers, and unchanged local GPU ledgers.

Current main: 12 pages, 42,217 extracted non-whitespace characters and 44,852 conservatively estimated characters. The estimate adds the four figures' 1,635 text characters again plus 1,000 for extraction uncertainty. Margin below 50,000: 5,148 characters. No template, font or spacing adjustment was used.

Pages 1, 2, 3 and 12 were rendered and inspected at 144 dpi. Edited passages, adjacent material, Figure 1 and references are readable without clipping. All four figures and three tables retain their numbers and pages. No unresolved references or overfull boxes occur. The archive independently compiles the main and unchanged companion and reproduces delivered PDF text. Official dependencies are included beside the manuscript, incorporating the prior requested compilation repair.

The historical consolidation report is preserved unchanged. It is not rerun as an assertion that intentional prose changes have identical page pixels. The current checks are in `paper/icaart2027/verification.json` and `source_archive_verification.json`.

No experiments, new figures, carrier generation or GPU inference ran. Zero GPU seconds were added. Existing permission and venue-policy questions remain unchanged.

## Reproduction

```sh
python -B paper/icaart2027/build.py --target main
../llm-rankcloak/.venv/bin/python -B paper/icaart2027/verify.py
python -B paper/icaart2027/package_source.py
```

## Revised abstract

We encode a small image within generated text and a text message within an image, allowing a recipient with the required key and model configuration to recover the original content. Encryption protects the content, while steganographic encoding places it within another medium. A language model assigns probabilities to text choices, and a pixel autoregressive model does the same for pixel values. Encoding rules use these choices to carry information, and the receiver reconstructs the mapping from the saved file. We develop a shared authenticated protocol for exact recovery of standardized grayscale image pixels and literal text from actual text and PNG files. An extension preserves an existing photograph through small pixel changes. Controlled evaluations measure recovery, capacity, detection and execution cost. Across 120 transmissions, fixed and entropy-gated coding each recover 20/20 payloads in both directions. Arithmetic coding recovers 20/20 PNG payloads but 0/20 text payloads because insufficient information accumulates before the length limit. The photograph extension recovers 20/20 held-out messages, but learned ranks do not outperform simple parity. Detection results depend on the observer's context, and a matched development benchmark reduces encoding and decoding latency by 5.13 times using CUDA graphs.

## Revised Introduction opening

A sender may wish to send a small image through a text passage or place a short message within a photograph. The hidden content is the payload, and the visible passage or image is its carrier. A recipient with the required key and model configuration must recover the exact represented image pixels or message bytes from that carrier. Generative models make many plausible text or pixel choices available, but those choices must carry information in a way the recipient can reconstruct. Recovery from the saved file matters because the recipient receives the passage or pixels, not the sender's internal decisions.

## Revised Method opening

We first represent a standardized source image or literal message as bytes and place them in a fixed-size encrypted and authenticated packet. The chosen coding rule maps packet information to text choices made with a language model or pixel choices made with a pixel autoregressive model. The receiver reads the saved text or PNG and uses the key, shared context and model configuration to reconstruct and authenticate the packet. A separate evaluator compares the recovered bytes with the source to establish exact recovery. The photograph extension instead constrains changes to an existing image and rebuilds its rank mapping from the preserved image context.
