# Research Methodology

## 1. Research Objective and Questions

This evaluation documents AgentChain's controlled methods for selecting security tests, discovering and validating compositional attack chains, evaluating a local multi-agent scenario, and replaying chains after mitigation. It addresses the following questions:

1. Under a common three-test budget, do the Day 7 static and adaptive methods produce the same controlled discovery and validation outcomes, and what differences are observed in LLM calls and measured execution time?
2. How do the four Day 12 planner configurations select tests and use fallback under the same initial scenario state?
3. Can the controlled sandbox reproduce registered attack-chain steps and the two-agent V11-to-V10 scenario?
4. In same-chain replay, does the selected control block at least one evaluated step, and which steps remain vulnerable?

These are descriptive controlled-evaluation questions. The available experiments do not provide inferential statistical analysis or support claims of general superiority.

## 2. Experimental Scope and Safety Boundaries

The vulnerability and replay experiments run against AgentChain's intentionally vulnerable, deterministic sandbox test functions. The sandbox executor accepts a fixed set of test names and returns controlled findings and evidence; mitigation is applied through registered local controls. The Day 14 multi-agent implementation describes its scenario as synthetic and local-only, and uses a local agent registry rather than network communication.

The Day 7 and Day 12 planner evaluations are distinct from complete end-to-end security evaluations. In particular, Day 12 records planner selections, budget use, and fallback decisions; it does not execute sandbox tests to measure discovery or mitigation outcomes. The Day 16 evaluation and project regression test counts are software-test evidence, not attack-discovery or security-effectiveness metrics.

No experiment described here evaluates production agents, real users, external targets, or real-world security impact. Controlled sandbox results do not demonstrate real-world security effectiveness.

## 3. System Under Evaluation

AgentChain combines deterministic sandbox tests, a fixed-sequence static baseline, an adaptive planner, registered chain definitions, a validator, a local two-agent scenario, and mitigation/replay utilities.

The static baseline executes the predefined sequence `permission_test -> tool_access_test -> memory_access_test`. Adaptive runs receive a planner input and supply selected tests to the same sandbox/chain-validation path. Registered chains specify ordered steps and dependencies; the validator checks that each step completes, reproduces its expected finding, has evidence, and satisfies dependency ordering.

The Day 14 multi-agent scenario constructs two local agents and controlled communication, then invokes the V11 cross-agent trust and V10 unsafe delegation vulnerability scenarios. The chain is considered triggered when both vulnerability scenarios report vulnerable and the controlled message is delivered. A validator checks the chain identifier, communication result, vulnerability states, and exact V11-then-V10 order.

Implementation references for the mechanisms described here include [the static baseline](sandbox/baseline/static_baseline.py), [the sandbox executor](sandbox/execution/sandbox_executor.py), [the chain definitions](sandbox/chains/chain_definitions.py), [the chain validator](sandbox/validator/chain_validator.py), [the controlled multi-agent scenario](sandbox/agent/multi_agent_security.py), and [the mitigation replay executor](sandbox/chains/chain_replay_executor.py).

## 4. Experimental Design

The designs use controlled inputs, explicit budgets where available, and separate reporting of planner observations, sandbox outcomes, and software tests.

| Study | Design and controlled conditions | Scope of measurement |
|---|---|---|
| Day 7 static vs adaptive | Same registered three-step scenario and equal maximum budget of 3 tests; the controlled runner supplies three predetermined adaptive responses | Test/finding/chain/validation counts, LLM calls, fallback status, and recorded test execution cost |
| Day 12 A/B/C/D ablation | Scenario `DAY11-COMMON-001`, seed 42, maximum 3 tests, maximum 3 LLM calls, configured time budget of 30 seconds; same initial scenario state across configurations | Planner selection, budget fields, selection accuracy, fallback count, and status; execution-dependent outcomes are N/A |
| Day 14 multi-agent | Controlled two-agent local scenario; V11 cross-agent trust followed by V10 unsafe delegation; controlled message delivery | Whether the V11 -> V10 scenario triggers and validates in order |
| Day 15 correct-control replay | Four registered chains; baseline execution, one selected control, and replay of the same chain | Chain validation before/after, blocked steps, disruption, and residual vulnerable steps |
| Initial ineffective-control replay | Five chains evaluated with `memory_validation` selected | Whether that control disrupts each chain and which steps remain vulnerable; ineffective cases are retained |
| Day 16 and project regressions | Software evaluation and regression suites | Test pass/failure counts and warnings only; not security-experiment outcomes |

Each reported result is interpreted only within its experiment's scope. No sample size, repeated-trial estimate, confidence interval, or significance test is inferred beyond the recorded runs.

## 5. Static Versus Adaptive Evaluation

Day 7 compares the static and adaptive approaches under the same chain scenario and an equal test budget of three. The static baseline uses a fixed ordered sequence. The adaptive runner applies a three-test cap, runs the adaptive loop, and then submits the selected sequence to the chain validator. The controlled orchestration replaces the planner's JSON-generation call with a supplied three-response sequence, making this a controlled deterministic planner run rather than evidence about live remote API behavior.

The comparison records tests executed, findings, candidate and validated chains, average chain length, validation rate, LLM calls, fallback status, and measured execution time. Static and adaptive runs are compared only when both completed and their test budgets match. The reported Day 7 outcome is equal discovery and validation under the equal budget; it does not establish adaptive superiority.

The static baseline's test execution and its subsequent chain-validation replay are distinct operations in the implementation. Reported evaluation fields and timing are taken from the run records described by the Day 7 evaluation code, not interpreted as a comprehensive end-to-end service latency.

## 6. Four-Configuration Ablation Methodology

Day 12 invokes the existing planner ablation suite through the common Day 11 scenario runner and passes the raw result to the Day 12 metric calculator. The runner defines the common scenario, records the seed and budgets, and reports that the same initial state was used. The tested configurations are:

| Configuration | Planner components | RAG enabled | Chain context enabled |
|---|---|---:|---:|
| A | LLM-only | No | No |
| B | LLM + RAG | Yes | No |
| C | LLM + chain context | No | Yes |
| D | LLM + RAG + chain context | Yes | Yes |

The expected sequence is `permission_test -> tool_access_test -> memory_access_test`. Selection accuracy is calculated only when expected tests are supplied: the implementation compares corresponding positions and divides the correct-position count by the smaller of the expected and selected sequence lengths. For the reported full-length three-test sequence, this yields the recorded sequence-selection metric. The definition is positional agreement over compared entries, not a separate end-to-end discovery or security-success rate.

Fallbacks are counted from planner decisions: an explicit `fallback=true` decision is counted; otherwise a decision whose reason text contains "fallback" is counted. Budget use and selected tests may be reported from planner output. Metrics that require sandbox executionâ€”including tests executed, vulnerabilities or chains discovered, mitigation, replay, and associated timingâ€”are N/A in this planner-only comparison. The study does not establish that any configuration is superior.

## 7. Controlled Vulnerability and Attack-Chain Evaluation

The sandbox's registered chain definitions associate test names with ordered steps, vulnerability identifiers, and dependencies. For example, `CHAIN-AUTH-TOOL-MEM` orders `permission_test`, `tool_access_test`, and `memory_access_test`, with later steps depending on earlier ones. The registry verifies that steps are allowed sandbox tests and that dependency order is valid.

For a chain-validation run, the validator executes the candidate test sequence. A step is valid when its execution status is `completed`, its finding equals the expected finding for that test, evidence is present, and dependencies are satisfied. A chain's validation rate is the number of valid steps divided by the number of returned steps; the overall status is validated only when there is at least one step and every step is valid.

This validates reproduction of the defined controlled findings and chain order. It does not assess prevalence, exploitability, or security of real systems. Multi-agent V11 -> V10 validation is a separate local scenario and is not conflated with the registered permission/tool/memory chain experiments.

## 8. Multi-Agent Evaluation Methodology

The Day 14 scenario builds a local registry containing an untrusted Research agent and a controlled Planning agent. The scenario configures the sender's allowed interaction with the receiver, sends a synthetic controlled delegation request, and invokes the V11 cross-agent trust and V10 unsafe delegation scenarios. The expected order is V11 -> V10.

The chain-triggered condition requires both V11 and V10 to be vulnerable and the message status to be delivered. The scenario validator checks the chain ID, triggered state, delivered communication, vulnerable status for each finding, and exact ordered vulnerability IDs. This is a controlled two-agent demonstration with explicit local communication rules, not a multi-agent deployment or broad sample of agent interactions.

## 9. Mitigation, Same-Attack Replay, and Validation

The chain replay implementation clears mitigation state, executes all steps of a registered chain as the baseline, validates baseline step evidence, applies one registered control, and executes the same chain steps again. It identifies a step as blocked only when the replay result has `mitigation_applied=true` and its evidence reports `result="attack_blocked"`. Every replayed step not meeting that condition is included in the residual vulnerable-step list. A chain is marked disrupted when at least one step is blocked.

For the correct-control replay, four chains were evaluated: all four were disrupted, with eight residual vulnerable steps remaining. Disruption therefore means interruption of each evaluated chain under the recorded rule; it does not mean that all vulnerabilities were removed. The initial `memory_validation` replay also remains part of the evaluation: CHAIN-A, CHAIN-C, and CHAIN-E were ineffective-control cases with no disruption; CHAIN-B and CHAIN-D were disrupted at `memory_access_test` but retained vulnerable steps.

The replay validator reports a validated mitigation replay only when baseline validation and post-mitigation validation both pass and at least one step is blocked. Its chain-level validation rate is binary for that replay: 1.0 when those conditions pass and 0.0 otherwise. This is distinct from both per-step validation rate and chain-disruption rate. A wrong control can be applied while the attack chain continues, producing no blocked steps and failed replay validation.

## 10. Metric Definitions and Calculation Rules

The following definitions follow the implementation where its calculation logic is explicit. All rates are interpreted with their own denominators and are not interchangeable.

| Metric | Calculation or rule | Interpretation |
|---|---|---|
| Tests executed | Number of executed test entries recorded for an experiment | Work performed in the recorded run; for Day 12 planner-only output, execution count is N/A |
| Findings | Number of finding entries recorded | Count of controlled findings, not a measure of real-world vulnerability prevalence |
| Candidate chains | Number of candidate-chain entries recorded | Chains proposed/constructed before the validation distinction |
| Validated chains | Number of validated-chain entries recorded | Candidate chains meeting the experiment's validation condition |
| Average chain length | Arithmetic mean of the chain lengths recorded for the observations in scope | Descriptive average for those observations |
| Per-step chain validation rate (`ChainValidator`) | Valid steps / returned chain steps; a step requires completed status, expected finding, evidence, and valid dependency order | Reproduction and structural validation within the controlled sandbox |
| Day 7 validation rate | The rate returned by chain validation for the selected sequence; adaptive evaluation averages the supplied sequence validation rates | Not a discovery rate or mitigation rate |
| Day 12 selection accuracy | Correct positional matches / `min(expected sequence length, selected sequence length)`, when the denominator is nonzero and expected tests are supplied | Planner sequence agreement over compared positions; not sandbox discovery |
| Fallback count | Count of decisions explicitly marked as fallback, or with "fallback" in the reason when no explicit true flag counted that decision | Planner fallback observations; not API error count |
| LLM calls | Planner call count recorded by the run or budget fields | Call count only; not latency or quality |
| Chain-disruption rate | Disrupted replay chains / evaluated replay chains with mitigation evidence; in chain replay, a chain is disrupted if at least one step is blocked | Interruption rate under this operational definition |
| Blocked-step rate | Blocked steps / total evaluated chain steps | Fraction of chain steps blocked, not fraction of all vulnerabilities mitigated |
| Residual vulnerable steps | Sum of unblocked replay steps across evaluated chains | Vulnerable steps remaining after the selected control |
| Mitigation validation rate | Validated mitigation replays / applicable mitigation trials; replay validation requires valid before/after chains and disruption | Validation of the replay procedure, not proof that every vulnerability was removed |
| Vulnerability-mitigation rate | N/A unless a separately defined and measured vulnerability-removal outcome is available | Must not be substituted with chain-disruption rate |
| Execution time | Sum of per-test `execution_time_seconds` values recorded around the sandbox test call where the relevant evaluator aggregates execution costs | Measured test execution cost, not a general end-to-end latency |

The research dataset stores experiment records and its summaries aggregate counts and arithmetic means by static/adaptive mode. Some generic metric structures initialize empty aggregates to numeric zero; this is a data-structure default, not evidence that an unmeasured outcome was zero. This report uses N/A when the experiment did not measure a metric. In particular, four disrupted chains and eight residual steps do not support a claim that 100% of vulnerabilities were mitigated.

## 11. Timing and Performance Measurement

The sandbox executor records elapsed time around each deterministic `run_test` invocation using a performance counter and records a test count of one. Baseline and adaptive evaluators aggregate available per-test execution-cost fields. Day 7 reports approximately 0.0000128 seconds for static execution and approximately 0.0000824 seconds for adaptive execution in the documented controlled run. These values are specific to the recorded execution and are not general performance estimates.

Day 12 includes a configured time budget of 30 seconds and can report planner budget time if present, but the verified experiment did not record a usable selection timing result. Its selection timing, RAG latency, and end-to-end experiment time are N/A. Day 15 replay latency is N/A where not recorded. Day 16's 74.29 seconds is the evaluation test-suite runtime, not the runtime of a security experiment. No additional timing measurement is inferred.

## 12. LLM/API Fallback and Failure-Case Handling

Day 12 fallback counts are A=2, B=0, C=1, and D=1. Gemini/API availability affected some runs. The available evidence does not reliably map specific 503/429 responses to individual configurations; no additional API logs or configuration-level error mapping are assumed. Day 7 reports `fallback=false` for both methods, and its controlled runner supplies predetermined planner responses.

Failure outcomes remain part of the report rather than being filtered from comparisons. The initial replay records CHAIN-A, CHAIN-C, and CHAIN-E as chains not disrupted by the selected `memory_validation` control. CHAIN-B and CHAIN-D were disrupted at `memory_access_test` but retained residual vulnerable steps. Wrong-control replay is retained as a failure case because the attack may continue and replay validation may fail. Failed or ineffective outcomes must not be recoded as successful mitigation.

Missing or unrecorded values are reported as N/A, never as zero. API errors are described only at the level supported by the available evidence.

## 13. Reproducibility and Recorded Configuration

| Study | Recorded reproducibility information |
|---|---|
| Day 7 | Equal static/adaptive test budget of 3; controlled scenario `CHAIN-AUTH-TOOL-MEM`; experiment configuration records seed 42; controlled runner supplies three adaptive responses |
| Day 12 | Scenario `DAY11-COMMON-001`; seed 42; maximum 3 tests; maximum 3 LLM calls; configured time budget of 30 seconds; same initial scenario state across A-D |
| Day 14 | Controlled two-agent local scenario; chain order V11 -> V10; communication result and vulnerability states are included in the scenario record |
| Day 15 | Registered chain ID, selected control, baseline step results, post-control replay results, blocked steps, residual steps, and validation outcomes are included in replay records |
| Day 16 evaluation | 44 passed, no evaluation test failures, one dependency deprecation warning; suite runtime 74.29 seconds |

Fallback counts and unsuccessful replay outcomes are retained as described in Section 12. The available evidence does not establish model versions or knowledge-base versions, nor random seeds for experiments other than the recorded Day 7 and Day 12 configurations. Unrecorded parameters and performance measurements are N/A rather than inferred.

The implementation references include [Day 7 configuration](sandbox/evaluation/day7_controlled_experiment.py), [Day 7 static runner](sandbox/evaluation/day7_static_run.py), [Day 7 adaptive runner](sandbox/evaluation/day7_adaptive_run.py), [Day 7 comparison](sandbox/evaluation/day7_comparison.py), [Day 12 common scenario runner](sandbox/evaluation/day11_ablation_scenario_runner.py), [Day 12 experiment wrapper](sandbox/evaluation/day12_ablation_experiment.py), [Day 12 metric calculations](sandbox/evaluation/day12_ablation_metrics.py), [research dataset structure](sandbox/evaluation/research_dataset.py), [research metrics](sandbox/evaluation/research_metrics.py), [research result schema](sandbox/evaluation/research_result.py), and [research summaries](sandbox/evaluation/research_summary.py).

## 14. Limitations and Threats to Validity

- **Sandbox scope:** The vulnerability and chain behaviors are controlled synthetic tests in an intentionally vulnerable sandbox. Their outcomes do not establish real-world security effectiveness.
- **Small controlled evaluation set:** Day 7 compares a single reported controlled run per method; Day 12 observes four configurations in one common planner scenario; Day 14 evaluates a specified two-agent chain; and the correct-control replay covers four chains. Broad generalization is not supported.
- **Planner-only versus end-to-end scope:** Day 12 selection and fallback observations do not include sandbox discovery, mitigation, same-attack replay, or execution timing. They cannot be treated as end-to-end security outcomes.
- **API availability:** Gemini/API availability affected some Day 12 runs. Fallback counts are recorded, but 503/429 responses cannot be reliably attributed to particular configurations from the available evidence.
- **Residual vulnerabilities:** Correct-control replay disrupted all four evaluated chains but left eight vulnerable steps. Initial ineffective-control cases further show that control selection matters in these scenarios.
- **Metric construct validity:** Chain validation verifies expected findings, evidence, and dependency order; it does not establish a real-world exploit. Chain disruption requires only one blocked step by the replay implementation and is not equivalent to eliminating every vulnerability.
- **Incomplete performance evidence:** Day 7 per-test execution cost is available, but Day 12 selection timing, RAG latency, end-to-end time, and Day 15 replay latency are N/A where not recorded. The Day 16 suite runtime is software-test duration, not security-experiment latency.
- **No inferential claim:** The verified evidence supplies descriptive outcomes, not repeated-sample estimates or statistical significance. Neither adaptive planning nor any ablation configuration is shown to be superior.
- **Reporting and implementation defaults:** Generic aggregators may initialize empty fields to zero. Such defaults are not treated as observed measurements; unavailable evidence is reported as N/A.

Accordingly, this methodology supports reproducible description of the stated controlled behaviors only. It does not support claims of comparative superiority or real-world security effectiveness.
