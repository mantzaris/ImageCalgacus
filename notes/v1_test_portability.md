# V1 CPU test portability

Accepted starting checkout: 29d2ca2ff7e0cdf6f3a6c000d1ad7948ac8a7bc3, clean before this task. This cleanup changes tests, not coding, model inference, distributions, serialization or historical outcomes. Subsequent V2 accounting/continuation changes are a separate authorized engineering stage.

## Reproduction and correction

A clean git export with no runs/, .runtime/ or source cache reproduced three errors: historical-credit loading used original-machine carrier paths, packet-binding tests required the private baseline/keys, and receiver-resume tests copied original private reports/inboxes. Here the original process test passed, so the independently reported process-ID failure was not reproduced on this coherent execution host.

The pre-cleanup public suite ran 62 tests: 58 passed, three errors, one expected source-cache skip. The independently reviewed environment instead reported 57 passes, three errors, one process failure and one cache skip.

Ordinary continuation tests now create temporary real AES-GCM packets/keys, grayscale sources, contexts, profiles, saved carriers, reports and ledgers. They exercise the real binding, sender-state, terminal/event and pending-work functions. They reject altered/re-encrypted packets, incorrect keys, changed sources/contexts/profiles or extra inbox inputs, duplicate credits and inconsistent completions; they recover a terminal written before its event append. No historical private bytes were copied into tests.

Process accounting has two verification scopes:

- Deterministic unit fixtures supply controlled Linux-style process records and environments. Matching PID/start-time blocks reconciliation; a reused PID with a different start-time is not mistaken for the old child; a surviving budget marker still blocks it. Only a dead/unmatched process is conservatively charged, once.
- A separately identified Linux integration check starts a model-free child. It verifies Python and /proc agree on process identities, reads the child's budget marker, exercises both real survivor guards, then terminates/reaps the child and verifies one-time reconciliation. Unsupported/incoherent environments skip only this platform check with a specific reason. The production guards were not weakened or mocked in the real-host check.

Historical credit/original-packet checks moved to explicitly opt-in private integration. Set IMAGECALGACUS_PRIVATE_TESTS=1 only with the original private baseline, packet/key bindings and run files. Missing prerequisites then fail clearly rather than silently treating missing history as successful verification. Source-cache verification retains its existing explicit skip when the pinned cache is absent.

## Executed verification before V2 preparation

| Scope | Executed result |
|---|---|
| Clean export, corrected CPU suite | 64 tests: 62 passed, 2 skips (private historical integration, pinned source cache), no failures/errors; 7.537s |
| Clean export, public qualification verifier | Complete 152-unit allocation, 126 exact recoveries and 26 preserved failures; exit 0 |
| Original execution host, private checks enabled | All 64 CPU tests passed; 11.228s |
| Model-free Linux child integration | Passed both PID/start-time and environment-marker survivor guards; no neural inference |
| GPU cost of cleanup | 0 seconds |

Clean export path used: /tmp/imagecalgacus-public-cleanup-LoE4P4 (disposable; not a reproducibility dependency). It contained the accepted git archive plus the single corrected test file, with no private runtime material. The final V2 review will also verify a clean export of the completed working source.

Commands:

~~~sh
python -B -m unittest discover -s tests -v
IMAGECALGACUS_PRIVATE_TESTS=1 python -B -m unittest discover -s tests -v
python -B scripts/finalize_v1_qualification.py --verify-public artifacts/v1_qualification_review
~~~

Use a compatible CPU interpreter with the declared dependencies. The local checks used /home/meow/Documents/repos/llm-rankcloak/.venv/bin/python; that absolute path is not needed by the synthetic tests. Public source equality/coverage verification does not repeat GPU decoding or establish possession of private keys. Historical results and their original execution hashes remain unchanged.

## Final V2-source public/private verification

After all model work stopped, the completed working source and public artifacts were exported to /tmp/imagecalgacus-v2-final-public-EJPYql using git ls-files (tracked plus nonignored reviewable new files) and tar. No private runs/, .runtime/, models/, .deps-text or pinned source cache was included. PYTHONPATH and IMAGECALGACUS_PRIVATE_TESTS were unset for public commands.

| Final scope | Observed result |
|---|---|
| Clean export, full CPU suite including nine V2 checks | 73 tests: 71 passes, two explicit prerequisite skips; 7.628s |
| Local retained source cache/private integration enabled | 73/73 passed; 11.447s |
| Coherent Linux model-free child integration | Passed in both scopes |
| Clean export, V2 public verifier | Complete 120-unit allocation: 100 exact, 20 retained failures; 40 controls |
| Clean export, historical public verification | V0 10/10; V1 pilot 10 exact/2 failures; V1.2 5 exact/1 failure; qualification 126 exact/26 failures, all allocations complete |
| Clean export, frozen CPU analysis | Same statistical hash, three CSV files and two SVG plots as the execution checkout |
| Actual completed V2 continuation | No additional jobs, charges, packet changes or duplicate credits; 1,846 run/ledger files unchanged |

The nine new V2 tests cover allocation identity, method pairing, receiver-only pending work, realized control lengths, idempotent phase authorization, both budget ceilings and frozen grouped-analysis primitives. Existing packet, rank/gating/A1, RGB conditional, UTF-8, serializer, receiver boundary and arithmetic oracle tests remain passing.

No coding/probability/serialization change was needed. The new engineering changes are V2-only stage accounting and continuation routing. Original GPU jobs retain their historical source identities. Public equality/coverage checks are not private-key or model-backed replays; the latter evidence comes from the separately charged original GPU jobs, not these CPU verifications. [Final CPU verification records](../artifacts/v2_review/final_cpu_verification.json) and [V2 results](v2_results.md) preserve these distinctions.
