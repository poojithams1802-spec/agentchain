# Experimental Results

## 1. Experimental Setup

The evidence summarized here comes from controlled AgentChain experiments and test suites. Planner decisions, sandbox execution outcomes, chain validation, and software regression results are reported as distinct evidence types.

- **Day 7:** A controlled static-versus-adaptive evaluation with a test budget of three.
- **Day 12:** Saved A/B/C/D runner artifacts include both planner decisions and controlled sandbox executions. The runs are separately reported; fallback, budget exhaustion, and unequal completion make them invalid as a successful four-way LLM comparison.
- **Day 14:** A controlled two-agent sandbox scenario with controlled communication.
- **Day 15:** End-to-end controlled sandbox chain replay with selected controls.
- **Day 16 and regression suites:** Software evaluation evidence, reported as test results rather than security-effectiveness measurements.

All results are controlled sandbox results. They do not demonstrate real-world security effectiveness.

## 2. Static Baseline

The Day 7 static planner is the baseline for comparison. It used a budget of three tests, executed all three, reported three findings, and produced and validated one candidate chain of average length three. Its validation rate was 1.0. It made no LLM calls, did not fall back, and its measured execution time was approximately 0.0000128 seconds.

## 3. Adaptive Evaluation

In the same Day 7 controlled evaluation, the adaptive method used the same three-test budget and executed three tests. It reported three findings and produced and validated one candidate chain of average length three, with a validation rate of 1.0. It made three LLM calls, did not fall back, and its measured execution time was approximately 0.0000824 seconds.

## 4. Day 7 Static vs Adaptive Comparison

| Metric | Static | Adaptive |
|---|---:|---:|
| Test budget | 3 | 3 |
| Tests executed | 3 | 3 |
| Findings | 3 | 3 |
| Candidate chains | 1 | 1 |
| Validated chains | 1 | 1 |
| Average chain length | 3 | 3 |
| Validation rate | 1.0 | 1.0 |
| LLM calls | 0 | 3 |
| Fallback | false | false |
| Execution time | approximately 0.0000128 seconds | approximately 0.0000824 seconds |

Both methods used the same budget and produced the same controlled discovery and validation result. This experiment does not establish adaptive superiority. In this deterministic controlled run, the adaptive method incurred additional LLM calls and higher measured execution time.

## 5. Day 12 Ablation Study

The saved runner artifacts are not planner-only: both record sandbox execution results. They remain separate runs, and neither is a valid successful-LLM comparison across all four configurations.

### Saved run: `ai-engine/results/phase3_ablation_day12.json`

The artifact identifies `runner_scope` as `planner_plus_sandbox`, uses the same initial state across A-D, and records a three-test/three-LLM-call limit. Each configuration selected two of three requested tests, used fallback after Gemini HTTP 429 quota errors, made three LLM calls, and completed two sandbox executions. Each run ended `budget_exhausted`; `selection_accuracy` is null.

| Configuration | Selected / requested | LLM calls | Fallback | Completed sandbox executions | Status |
|---|---:|---:|---|---:|---|
| A | 2 / 3 | 3 | Yes | 2 | `budget_exhausted` |
| B | 2 / 3 | 3 | Yes | 2 | `budget_exhausted` |
| C | 2 / 3 | 3 | Yes | 2 | `budget_exhausted` |
| D | 2 / 3 | 3 | Yes | 2 | `budget_exhausted` |

These records demonstrate controlled fallback and sandbox execution, not successful LLM selection or comparative effectiveness.

### Saved run: `ai-engine/results/phase3_ablation_gemini_20261011.json`

This artifact also records `planner_plus_sandbox` and a common initial state, but completion differs by configuration. A and D each made one non-fallback decision, selected one of three tests, executed one sandbox test, and ended `budget_exhausted` at 30.952956 s and 31.074635 s respectively. B and C used fallback for all three decisions after HTTP 503 (B) and HTTP 503/504 (C), selected and executed all three tests, and ended `completed` at 12.634323 s and 23.548119 s respectively. Each configuration has at least one completed sandbox execution; the run is nevertheless not a valid A/B/C/D comparison because successful non-fallback reasoning and equivalent completion are absent. Accuracy is null.

Earlier `*_before_deadline_fix.json` and `*_before_eval_fix.json` files remain historical snapshots, not replacements for the saved run above. The separate narrative in `P3_day16_experimental_results.md` gives different times and says all configurations used fallback and selected three tests; those figures do not match either saved JSON record and are retained as an unresolved, unverified report rather than merged into these results. Another earlier narrative reports positional agreement 1.0 and fallback-decision counts A=2, B=0, C=1, D=1; its raw source record is not identified in the current artifacts. Positional agreement is not successful-LLM accuracy or evidence of superiority.

The derived `phase3_ablation_evaluation_20261011.json` names the Gemini runner JSON as its source and marks `performance_comparison_valid: false`. It reports selection accuracy A=0.3333, B/C/D=1.0 and fallback-decision counts A=0, B=2, C=3, D=3; it also explicitly says accuracy was copied from the source and not independently validated. These are reported derived metrics, not verified ground-truth accuracy. They differ from the older narrative counts A=2, B=0, C=1, D=1, which remain unmatched to a raw record.

No valid live non-fallback A/B/C/D comparison is present. Mitigation, same-chain replay, and broader security-effectiveness outcomes are not measured by these ablation artifacts and remain **N/A**.

## 6. Multi-Agent Results

| Scenario | Agents and communication | Evaluated vulnerabilities | Validated chain order |
|---|---|---|---|
| Day 14 controlled two-agent sandbox | Two agents; communication was controlled | V11 cross-agent trust; V10 unsafe delegation | V11 -> V10 |

This result records the validated chain order in the stated controlled scenario. Other multi-agent metrics are **N/A**.

The saved Day 14 scenario validates that the V11→V10 chain triggers under controlled communication. It does not apply a mitigation or replay the multi-agent chain, so multi-agent chain disruption is **N/A**, not inferred from the separate registered-chain replay results. Section 18's multi-agent disruption criterion is therefore **Not Verified**.

## 7. Chain Mitigation and Replay Results

The Day 15 correct-control replay evaluated four chains. Each selected control blocked a step and disrupted its evaluated chain, but vulnerable steps remained in every chain. Chain disruption is not equivalent to complete vulnerability mitigation.

| Chain | Selected control | Blocked step | Chain disrupted | Residual vulnerable steps | Validation rate |
|---|---|---|---|---|---:|
| CHAIN-A | `authorization_gate` | `permission_test` | Yes | `tool_access_test` | 1.0 |
| CHAIN-B | `memory_validation` | `memory_access_test` | Yes | `permission_test`, `tool_access_test` | 1.0 |
| CHAIN-C | `tool_allowlist` | `tool_access_test` | Yes | `prompt_injection_test`, `sensitive_data_test` | 1.0 |
| CHAIN-D | `memory_validation` | `memory_access_test` | Yes | `permission_test`, `tool_access_test`, `unsafe_delegation_test` | 1.0 |

| Aggregate replay metric | Result |
|---|---:|
| Chains evaluated | 4 |
| Chains disrupted | 4/4 |
| Chain disruption rate | 100% |
| Total chain steps | 12 |
| Blocked steps | 4 |
| Blocked-step rate | 33.3% |
| Residual vulnerable steps | 8 |
| Average residual vulnerable steps per chain | 2.0 |
| Average chain length | 3.0 |
| Before validation | 100% |
| After validation | 100% |

The 100% result applies only to chain disruption in these four evaluated replays. Eight residual vulnerable steps remained across the chains; this must not be interpreted as 100% of vulnerabilities being mitigated.

## 8. Failure Cases and Fallback Results

The initial controlled replay used `memory_validation` as the selected control. Its outcomes are separate from the later correct-control replay reported in Section 7.

| Initial replay chain | Selected control | Outcome | Residual vulnerable steps |
|---|---|---|---|
| CHAIN-A | `memory_validation` | Not disrupted; ineffective control | `permission_test`, `tool_access_test` |
| CHAIN-B | `memory_validation` | Disrupted at `memory_access_test`; residual vulnerabilities remained | `permission_test`, `tool_access_test` |
| CHAIN-C | `memory_validation` | Not disrupted; ineffective control | Unsafe tool access, prompt injection, sensitive-data exposure |
| CHAIN-D | `memory_validation` | Disrupted at `memory_access_test`; residual vulnerabilities remained | Permission, tool access, unsafe delegation |
| CHAIN-E | `memory_validation` | Not disrupted; ineffective control | Prompt injection, sensitive-data exposure, unsafe delegation |

CHAIN-A, CHAIN-C, and CHAIN-E are ineffective-control cases: the selected control did not disrupt those chains. CHAIN-B and CHAIN-D were disrupted at the specified step, but still had residual vulnerable steps; they are not failed disruptions.

| Replay stage / case | Result |
|---|---|
| Initial replay, CHAIN-A / CHAIN-C / CHAIN-E | Ineffective controls; chains were not disrupted |
| Initial replay, CHAIN-B / CHAIN-D | Chains were disrupted at `memory_access_test`, with residual vulnerabilities |
| Later correct-control replay | All 4 of 4 evaluated chains were disrupted; 8 residual vulnerable steps remained (see Section 7) |
| Wrong-control replay | A wrong control can be applied while the attack chain continues and validation fails |

The saved `phase3_ablation_day12.json` records fallback for all configurations after HTTP 429 quota failures. In `phase3_ablation_gemini_20261011.json`, A and D each have one non-fallback decision followed by budget exhaustion; B and C used fallback for all three decisions after 503/504 failures. The derived evaluation JSON reports fallback-decision counts A=0, B=2, C=3, D=3, consistent with that source runner record; the separate narrative counts A=2, B=0, C=1, D=1 remain unmatched. Day 7 static and adaptive runs reported `fallback=false`.

## 9. Timing and Performance

| Measurement | Result |
|---|---|
| Day 7 static execution time | Approximately 0.0000128 seconds |
| Day 7 adaptive execution time | Approximately 0.0000824 seconds |
| `phase3_ablation_day12.json`: per-configuration LLM calls | 3 each |
| `phase3_ablation_day12.json`: sandbox executions | 2 completed per configuration |
| `phase3_ablation_gemini_20261011.json`: A / D total time | 30.952956 s / 31.074635 s |
| `phase3_ablation_gemini_20261011.json`: B / C total time | 12.634323 s / 23.548119 s |
| `phase3_ablation_gemini_20261011.json`: comparative selection accuracy | N/A |
| Day 15 replay latency | N/A where not recorded |
| Day 16 evaluation test-suite duration | 74.29 seconds |

The Day 12 timings belong to separate saved records and are not comparable: one is fully fallback-affected and budget-exhausted; the other mixes incomplete non-fallback A/D results with completed fallback B/C results. A and D exceed the configured 30-second value in the latter artifact. This is consistent with the budget acting as a between-step cutoff rather than a hard cancellation guarantee for in-flight work. No configuration speed or quality ranking is supported. The 74.29-second measurement is the evaluation test-suite runtime, not the runtime of a security experiment. In the measured Day 7 run, adaptive execution took longer and made more LLM calls than static execution.

## 10. Research Interpretation

Day 7 produced equal discovery and validation outcomes for static and adaptive methods under an equal three-test budget. These results do not establish adaptive superiority. Day 12's saved runner artifacts include sandbox execution, but show fallback, budget exhaustion, or unequal completion. The narrative positional-agreement record is not traceable to a current raw artifact; it does not establish successful-LLM accuracy or superiority. The saved runs provide controlled failure/fallback evidence, not a valid comparative A/B/C/D result.

The controlled multi-agent experiment validated the V11 -> V10 chain. In the later correct-control replay, four out of four evaluated chains were disrupted, but eight vulnerable steps remained. Chain disruption is not equivalent to complete vulnerability mitigation. Collectively, these observations support controlled system functionality, not superiority over alternatives or real-world security effectiveness.

## 11. Limitations

- The experiments were conducted in an intentionally vulnerable, controlled sandbox. They do not demonstrate real-world security effectiveness.
- The evaluation set is small and controlled: the Day 7 comparison used a three-test budget, the multi-agent result covers the stated V11 -> V10 scenario, and the correct-control replay covers four chains.
- Day 12's saved artifacts include sandbox execution records. Both are invalid as a successful A/B/C/D comparison: `phase3_ablation_day12.json` has fallback and budget exhaustion in all configurations; `phase3_ablation_gemini_20261011.json` mixes incomplete non-fallback A/D with fallback B/C. Neither ablation artifact measures mitigation or same-chain replay.
- Day 12 total times are not comparative performance evidence. The 20261011 artifact records A and D above the configured 30 seconds, so the budget is not demonstrated as a hard wall-clock cancellation deadline.
- Narrative Day 12 figures in `P3_day16_experimental_results.md` conflict with the saved JSON artifacts; these are preserved as unverified historical claims, not used as current metrics.
- Chain disruption left residual vulnerabilities: eight vulnerable steps remained across the four correct-control replays. The initial replay also includes three ineffective-control cases.
- Performance measurements are incomplete. The earlier Day 12 selection timing and valid comparative selection accuracy for the P3 fallback run are N/A; Day 15 replay latency is N/A where not recorded. The P3 total times do not establish comparative speed, and no component-specific RAG latency or valid comparative performance measure is available.
- Unmeasured values are reported as N/A, not as zero.

## 12. Reproducibility Notes

| Experiment | Available settings |
|---|---|
| Day 7 static/adaptive comparison | Equal test budget of 3 |
| `phase3_ablation_day12.json` | Same initial state across A-D; each selected 2/3 tests, used 3 LLM calls, fell back after HTTP 429, and completed 2 sandbox tests before `budget_exhausted` |
| `phase3_ablation_gemini_20261011.json` | Same initial state across A-D; 30-second configured time budget; A/D selected 1/3 non-fallback test and exhausted budget; B/C completed 3/3 with fallback after HTTP 503/504 |

The older evaluation markdown and `*_before_*` files are retained as historical records. The narrative value set in the P3 Day 16 report and the earlier fallback counts are not mapped to a current raw artifact; they are not silently substituted for the saved JSON. Failure cases remain included. Settings not present in verified evidence, including model and knowledge-base versions, are not specified. Unrecorded measurements are N/A.

Historical Day 16 evidence reports **44 passed** in its sandbox/evaluation suite (74.29 seconds). Current full regression evidence reports **290 passed** in the sandbox suite, **149 passed** in backend tests, and **264 passed** in the full AI-engine suite on the latest worktree. These are software test results, not security-effectiveness measurements.

AgentChain demonstrates a controlled, knowledge-guided framework for adaptive discovery, validation, mitigation, and evaluation of compositional attack chains in an intentionally vulnerable agentic-AI sandbox. The experiments establish system functionality and reproducible controlled behavior, but they do not by themselves establish superiority over alternative methods or real-world security effectiveness.
