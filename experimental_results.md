# Experimental Results

## 1. Experimental Setup

The evidence summarized here comes from controlled AgentChain experiments and test suites. Results are grouped by experiment type because planner-only observations do not measure end-to-end sandbox behavior.

- **Day 7:** A controlled static-versus-adaptive evaluation with a test budget of three.
- **Day 12:** Two separately recorded planner-only A/B/C/D observations: an earlier controlled ablation observation and a later P3 fallback/failure-case experiment. Their metrics are reported separately; neither provides execution-dependent security-effectiveness evidence.
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

Two Day 12 planner-only records are retained separately and must not be merged as one experiment.

### Record 1: Earlier P4 ablation observation

This controlled observation used scenario `DAY11-COMMON-001`, seed 42, a maximum of three tests, a maximum of three LLM calls, and the same initial state across A/B/C/D. Each configuration selected the expected sequence:
`permission_test -> tool_access_test -> memory_access_test`.
Each configuration recorded three tests and three LLM calls.

| Configuration | Components | Selected sequence | Earlier positional agreement | Tests | LLM calls | Fallback-decision count |
|---|---|---|---:|---:|---:|---:|
| A | LLM-only | `permission_test -> tool_access_test -> memory_access_test` | 1.0 | 3 | 3 | 2 |
| B | LLM + RAG | `permission_test -> tool_access_test -> memory_access_test` | 1.0 | 3 | 3 | 0 |
| C | LLM + chain context | `permission_test -> tool_access_test -> memory_access_test` | 1.0 | 3 | 3 | 1 |
| D | LLM + RAG + chain context | `permission_test -> tool_access_test -> memory_access_test` | 1.0 | 3 | 3 | 1 |

The earlier metric calculation is positional agreement with the expected sequence. It does not establish comparative successful-LLM selection accuracy, and it does not show that one configuration is superior.

### Record 2: Latest P3 fallback experiment

The later P3 record is a separate fallback/failure-case experiment. It reports that all configurations used fallback and selected the same three predefined tests:
`permission_test -> tool_access_test -> memory_access_test`.

| Configuration | Mode | Fallback used | LLM calls | Selected tests | Recorded total time |
|---|---|---:|---:|---|---:|
| A | `llm_only` | Yes | 3 | `permission_test`, `tool_access_test`, `memory_access_test` | 33.259872 seconds |
| B | `llm_rag` | Yes | 3 | `permission_test`, `tool_access_test`, `memory_access_test` | 9.740067 seconds |
| C | `llm_chain` | Yes | 3 | `permission_test`, `tool_access_test`, `memory_access_test` | 1.031228 seconds |
| D | `llm_rag_chain` | Yes | 3 | `permission_test`, `tool_access_test`, `memory_access_test` | 1.358138 seconds |

Gemini HTTP 503 and HTTP 429 failures occurred during this P3 run. P3 states that selection accuracy is not available as a valid comparative metric for this run. The elapsed totals are recorded observations for a fallback-affected run, not evidence that a configuration is faster or better. The configured planner time budget was 30 seconds; A's reported total time exceeds that value. This is recorded transparently and does not establish strict budget enforcement.

Both records are planner-only observations for this report. Execution-dependent discovery, mitigation, replay, and security-effectiveness metrics are **N/A**. Results from one record do not fill missing metrics in the other.

## 6. Multi-Agent Results

| Scenario | Agents and communication | Evaluated vulnerabilities | Validated chain order |
|---|---|---|---|
| Day 14 controlled two-agent sandbox | Two agents; communication was controlled | V11 cross-agent trust; V10 unsafe delegation | V11 -> V10 |

This result records the validated chain order in the stated controlled scenario. Other multi-agent metrics are **N/A**.

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

#### Record 1: Earlier P4 fallback-decision counts

The earlier counts are counts of fallback decisions observed in planner output. They are not a Boolean indicator that a configuration used fallback at any point.

| Configuration | Fallback-decision count |
|---|---:|
| A | 2 |
| B | 0 |
| C | 1 |
| D | 1 |

#### Record 2: Latest P3 fallback status

The separate P3 record reports fallback used for A, B, C, and D. A fallback-used status means fallback occurred for that configuration in that run; it is not the earlier count of fallback decisions. Gemini HTTP 503 and HTTP 429 failures are documented for the P3 run. For the earlier observation, Gemini/API availability affected some runs, but the available evidence does not reliably map specific 503/429 responses to individual configurations. No additional API logs or run-level mapping are available. The Day 7 static and adaptive runs reported `fallback=false`.

## 9. Timing and Performance

| Measurement | Result |
|---|---|
| Day 7 static execution time | Approximately 0.0000128 seconds |
| Day 7 adaptive execution time | Approximately 0.0000824 seconds |
| Day 12 Record 1: per-configuration LLM calls | 3 |
| Day 12 Record 1: selection timing | N/A |
| Day 12 Record 2 (P3): A `llm_only` total time | 33.259872 seconds |
| Day 12 Record 2 (P3): B `llm_rag` total time | 9.740067 seconds |
| Day 12 Record 2 (P3): C `llm_chain` total time | 1.031228 seconds |
| Day 12 Record 2 (P3): D `llm_rag_chain` total time | 1.358138 seconds |
| Day 12 Record 2 (P3): per-configuration LLM calls | 3 each |
| Day 12 Record 2 (P3): valid comparative selection accuracy | N/A |
| Day 15 replay latency | N/A where not recorded |
| Day 16 evaluation test-suite duration | 74.29 seconds |

The Day 12 P3 totals are reported only as recorded observations for a run in which all configurations used fallback after Gemini HTTP 503 and HTTP 429 failures. They are not evidence that one configuration is faster or better. The configured planner time budget was 30 seconds, while A's recorded total time was 33.259872 seconds; strict enforcement is not established by these observations. No component-specific RAG latency or valid comparative performance measure is available. The 74.29-second measurement is the evaluation test-suite runtime, not the runtime of a security experiment. In the measured Day 7 run, adaptive execution took longer and made more LLM calls than static execution.

## 10. Research Interpretation

Day 7 produced equal discovery and validation outcomes for static and adaptive methods under an equal three-test budget. These results do not establish adaptive superiority. Day 12 contains two separate planner-only records. In the earlier P4 observation, all four configurations selected the expected sequence and an earlier metric calculation reported positional agreement of 1.0; this does not establish comparative successful-LLM selection accuracy or configuration superiority. In the later P3 fallback experiment, all four configurations used fallback, selected the same predefined sequence, and P3 reports no valid comparative selection-accuracy metric. Its elapsed times are recorded observations only, not a ranking of configuration performance.

The controlled multi-agent experiment validated the V11 -> V10 chain. In the later correct-control replay, four out of four evaluated chains were disrupted, but eight vulnerable steps remained. Chain disruption is not equivalent to complete vulnerability mitigation. Collectively, these observations support controlled system functionality, not superiority over alternatives or real-world security effectiveness.

## 11. Limitations

- The experiments were conducted in an intentionally vulnerable, controlled sandbox. They do not demonstrate real-world security effectiveness.
- The evaluation set is small and controlled: the Day 7 comparison used a three-test budget, the multi-agent result covers the stated V11 -> V10 scenario, and the correct-control replay covers four chains.
- Day 12 has two distinct planner-only records: the earlier P4 observation records fallback-decision counts, while the later P3 experiment reports fallback used for all four configurations and Gemini HTTP 503/429 failures. Specific 503/429 responses cannot be reliably mapped to individual configurations in the earlier observation.
- Neither Day 12 record measures execution-dependent discovery, mitigation, replay, or security effectiveness. The later P3 total times are fallback-affected observations, not comparative performance evidence; configuration A's total exceeds the configured 30-second planner budget, and strict budget enforcement is not established.
- Chain disruption left residual vulnerabilities: eight vulnerable steps remained across the four correct-control replays. The initial replay also includes three ineffective-control cases.
- Performance measurements are incomplete. The earlier Day 12 selection timing and valid comparative selection accuracy for the P3 fallback run are N/A; Day 15 replay latency is N/A where not recorded. The P3 total times do not establish comparative speed, and no component-specific RAG latency or valid comparative performance measure is available.
- Unmeasured values are reported as N/A, not as zero.

## 12. Reproducibility Notes

| Experiment | Available settings |
|---|---|
| Day 7 static/adaptive comparison | Equal test budget of 3 |
| Day 12 Record 1: earlier P4 planner-only observation | Scenario `DAY11-COMMON-001`; seed 42; maximum 3 tests; maximum 3 LLM calls; same initial state across A-D |
| Day 12 Record 2: latest P3 fallback experiment | Same initial state across A-D; maximum 3 tests; maximum 3 LLM calls; configured planner time budget of 30 seconds; all four used fallback; 3 LLM calls each |

The earlier P4 record's fallback-decision counts are A=2, B=0, C=1, and D=1; these counts are distinct from the latest P3 record's Boolean fallback-used status of Yes for all four configurations. The later P3 run records Gemini HTTP 503 and HTTP 429 failures; the earlier record's specific responses cannot be reliably mapped to configurations. Failure cases are retained in Section 8 rather than omitted. Settings not present in the verified evidence, including model and knowledge-base versions and seeds for other experiments, are not specified. Unrecorded measurements are reported as N/A.

The Day 16 sandbox/evaluation test suite completed with **44 passed**, no evaluation test failures, and one dependency deprecation warning. Its runtime was 74.29 seconds. Current project regression evidence reports **287 passed** in the full sandbox regression and **94 passed** in the backend full regression, each with one warning. These are software test results, not security-effectiveness measurements.

AgentChain demonstrates a controlled, knowledge-guided framework for adaptive discovery, validation, mitigation, and evaluation of compositional attack chains in an intentionally vulnerable agentic-AI sandbox. The experiments establish system functionality and reproducible controlled behavior, but they do not by themselves establish superiority over alternative methods or real-world security effectiveness.
