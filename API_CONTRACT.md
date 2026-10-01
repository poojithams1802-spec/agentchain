# AgentChain API Contract

This document describes the backend API contract implemented in the current FastAPI service and the integration contracts used by the AI planner and sandbox modules.

Status legend:
- Implemented: live FastAPI endpoint in the current backend
- Integration contract: contract between backend and AI/sandbox modules; the backend currently integrates with these modules through their Python interfaces rather than exposing separate FastAPI endpoints

---

## 1. Experiment lifecycle statuses

The current experiment lifecycle in the backend is intentionally simple and beginner-friendly.

- `created`: experiment has been created but not started
- `running`: experiment is currently active
- `completed`: experiment execution and the current orchestration/validation flow have finished

These values are used by the experiment records stored in the MongoDB `experiments` collection.

---

## 2. Implemented FastAPI endpoints

### 2.1 GET /health

Health check endpoint.

Request:
- Method: GET
- Path: `/health`

Response:
```json
{
  "status": "ok"
}
````

---

### 2.2 POST /experiments

Creates a new experiment record.

Request JSON:

```json
{
  "name": "Experiment 001",
  "mode": "adaptive",
  "max_tests": 10
}
```

Required fields:

* `name`: string, minimum length 1
* `mode`: string, minimum length 1
* `max_tests`: integer greater than 0

Response JSON:

```json
{
  "experiment_id": "EXP001",
  "status": "created"
}
```

Notes:

* `experiment_id` is generated as `EXP` + a zero-padded numeric counter.
* The new document is stored in the MongoDB `experiments` collection.

---

### 2.3 GET /experiments

Returns all experiments.

Response JSON:

```json
[
  {
    "experiment_id": "EXP001",
    "name": "Experiment 001",
    "mode": "adaptive",
    "max_tests": 10,
    "status": "created"
  }
]
```

---

### 2.4 GET /experiments/{experiment_id}

Returns one experiment by ID.

Response JSON:

```json
{
  "experiment_id": "EXP001",
  "name": "Experiment 001",
  "mode": "adaptive",
  "max_tests": 10,
  "status": "created"
}
```

If the experiment does not exist:

* HTTP 404
* body: `{"detail": "Experiment not found"}`

---

### 2.5 GET /experiments/{experiment_id}/logs

Returns log entries for an experiment from the MongoDB `experiment_logs` collection.

Response JSON:

```json
[
  {
    "experiment_id": "EXP001",
    "message": "Experiment started",
    "timestamp": "2026-09-25T12:34:56.789012+00:00"
  }
]
```

Logs may include:

* `Experiment started`
* `Planner selected test: <test_name>`
* `Sandbox completed: <test_name>`
* `Candidate chain created: <chain_id>`
* `Chain validation completed: <status>`
* `Experiment completed`

If the experiment does not exist:

* HTTP 404
* body: `{"detail": "Experiment not found"}`

---

### 2.6 GET /experiments/{experiment_id}/findings

Returns findings for an experiment from the MongoDB `findings` collection.

Response JSON:

```json
[
  {
    "experiment_id": "EXP001",
    "test": "permission_test",
    "finding": "weak_permission_control",
    "severity": "high",
    "evidence": {
      "permission": "DENIED",
      "observed_behavior": "TOOL_ALLOWED"
    },
    "confidence": 1.0,
    "timestamp": "2026-09-25T12:34:56.789012+00:00"
  }
]
```

Current sandbox findings may include:

* `weak_permission_control`
* `unsafe_tool_access`
* `memory_validation_weakness`

If the experiment does not exist:

* HTTP 404
* body: `{"detail": "Experiment not found"}`

---

### 2.7 GET /experiments/{experiment_id}/chains

Returns attack-chain records for an experiment from the MongoDB `attack_chains` collection.

Response JSON:

```json
[
  {
    "chain_id": "CHAIN-d4f70fa4",
    "experiment_id": "EXP001",
    "name": "Adaptive Candidate Chain",
    "steps": [
      "permission_test",
      "tool_access_test",
      "memory_access_test"
    ],
    "timestamp": "2026-09-25T12:34:56.789012+00:00"
  }
]
```

The `chain_id` is a stable string identifier generated when the candidate chain is created.

If the experiment does not exist:

* HTTP 404
* body: `{"detail": "Experiment not found"}`

---

### 2.8 POST /experiments/{experiment_id}/start

Starts and executes an experiment using the current P2 orchestration flow.

Behavior:

1. Verify the experiment exists.
2. Update the experiment status to `running`.
3. Insert a log: `"Experiment started"`.
4. Build the planner input using the current experiment findings and execution state.
5. Call the P3 adaptive planner through its Python interface.
6. Use the planner decision to select the next available sandbox test.
7. Execute the selected test through the P4 sandbox executor.
8. Store the resulting finding in MongoDB.
9. Store orchestration logs.
10. Repeat until the test budget is reached or no further test can be selected.
11. Create a candidate attack chain from the executed test sequence.
12. Validate the candidate chain using the P4 `ChainValidator`.
13. Store the validation result in the MongoDB `evaluation_results` collection.
14. Update the experiment status to `completed`.
15. Insert a log: `"Experiment completed"`.

Current adaptive sandbox tests are:

* `permission_test`
* `tool_access_test`
* `memory_access_test`

Response JSON:

```json
{
  "experiment_id": "EXP010",
  "status": "completed",
  "executed_tests": [
    "permission_test",
    "tool_access_test",
    "memory_access_test"
  ],
  "findings_created": 3,
  "sandbox_results": [
    {
      "status": "completed",
      "test": "permission_test",
      "finding": "weak_permission_control",
      "severity": "high",
      "evidence": {
        "permission": "DENIED",
        "observed_behavior": "TOOL_ALLOWED"
      },
      "confidence": 1.0
    }
  ],
  "candidate_chain": {
    "chain_id": "CHAIN-d4f70fa4",
    "steps": [
      "permission_test",
      "tool_access_test",
      "memory_access_test"
    ]
  },
  "validation_result": {
    "chain_id": "CHAIN-d4f70fa4",
    "status": "validated",
    "validated_steps": 3,
    "total_steps": 3,
    "chain_length": 3,
    "validation_rate": 1.0,
    "all_findings_reproduced": true
  }
}
```

Notes:

* The actual test sequence is selected through the adaptive planner and constrained by the available sandbox tests.
* The backend passes the agreed P3 planner fields without renaming them.
* Planner fallback behavior remains inside the P3 planner module.
* P2 does not modify the planner's decision schema.
* Candidate chain validation is performed using the P4 validator.
* Validation results are stored in the `evaluation_results` collection.

If the experiment does not exist:

* HTTP 404
* body: `{"detail": "Experiment not found"}`

---

### 2.9 GET /experiments/{experiment_id}/status

Returns the current status of the experiment.

Response JSON:

```json
{
  "experiment_id": "EXP001",
  "status": "completed"
}
```

If the experiment does not exist:

* HTTP 404
* body: `{"detail": "Experiment not found"}`

---

### 2.10 POST /chains/{chain_id}/validate

Validates a stored candidate attack chain using the P4 `ChainValidator`.

Behavior:

1. Check whether the chain exists in the MongoDB `attack_chains` collection.
2. Retrieve the experiment ID and stored chain steps.
3. Pass the chain steps to `ChainValidator`.
4. Validate each step against the expected finding, evidence, and dependency requirements.
5. Store the validation result in the MongoDB `evaluation_results` collection.
6. Return the structured validation result.

Response JSON:

```json
{
  "chain_id": "CHAIN-d4f70fa4",
  "status": "validated",
  "validated_steps": 3,
  "total_steps": 3,
  "chain_length": 3,
  "validation_rate": 1.0,
  "all_findings_reproduced": true,
  "steps": [
    {
      "test": "permission_test",
      "status": "completed",
      "finding": "weak_permission_control",
      "expected_finding": "weak_permission_control",
      "finding_matches": true,
      "severity": "high",
      "evidence_exists": true,
      "dependency_valid": true,
      "dependency_error": null,
      "valid": true
    }
  ]
}
```

The validation result can contain one step entry for every test in the candidate chain.

Validation checks include:

* expected finding matches the observed finding
* evidence exists
* chain dependencies are satisfied
* each step is valid

If the chain does not exist:

* HTTP 404
* body: `{"detail": "Chain not found"}`

---

### 2.11 GET /analytics

Returns aggregate metrics based on the existing MongoDB collections.

Response JSON:

```json
{
  "total_experiments": 10,
  "total_findings": 16,
  "total_chains": 3,
  "total_evaluation_results": 7
}
```

Current metrics:

* `total_experiments`: number of experiment records
* `total_findings`: number of finding records
* `total_chains`: number of attack-chain records
* `total_evaluation_results`: number of stored evaluation results

---

## 3. Shared data model notes

### Experiment record

```json
{
  "experiment_id": "EXP001",
  "name": "Experiment 001",
  "mode": "adaptive",
  "max_tests": 10,
  "status": "created"
}
```

### Finding record

```json
{
  "experiment_id": "EXP001",
  "test": "permission_test",
  "finding": "weak_permission_control",
  "severity": "high",
  "evidence": {
    "permission": "DENIED",
    "observed_behavior": "TOOL_ALLOWED"
  },
  "confidence": 1.0,
  "timestamp": "2026-09-25T12:34:56.789012+00:00"
}
```

### Log record

```json
{
  "experiment_id": "EXP001",
  "message": "Experiment started",
  "timestamp": "2026-09-25T12:34:56.789012+00:00"
}
```

### Chain record

```json
{
  "chain_id": "CHAIN-d4f70fa4",
  "experiment_id": "EXP001",
  "name": "Adaptive Candidate Chain",
  "steps": [
    "permission_test",
    "tool_access_test",
    "memory_access_test"
  ],
  "timestamp": "2026-09-25T12:34:56.789012+00:00"
}
```

### Evaluation result record

```json
{
  "experiment_id": "EXP001",
  "chain_id": "CHAIN-d4f70fa4",
  "status": "validated",
  "validated_steps": 3,
  "total_steps": 3,
  "chain_length": 3,
  "validation_rate": 1.0,
  "all_findings_reproduced": true,
  "timestamp": "2026-09-25T12:34:56.789012+00:00"
}
```

---

## 4. AI planner integration contract

Status: Integration contract.

The backend does not currently expose `/ai/plan` as a separate FastAPI endpoint. P2 currently integrates with the P3 planner through its Python interface.

### 4.1 Planner input

The P2 orchestration passes the following fields to the P3 `PlannerInput` model:

```json
{
  "findings": [
    {
      "finding": "Unexpected tool access",
      "severity": "high",
      "confidence": 0.9,
      "evidence": "Permission check failed"
    }
  ],
  "previous_tests": [
    "permission_test"
  ],
  "available_tests": [
    "tool_access_test",
    "memory_access_test"
  ],
  "retrieved_knowledge": [
    "Least privilege policy",
    "Tool access restrictions"
  ],
  "chain_state": {
    "experiment_id": "EXP001",
    "executed_tests": [
      "permission_test"
    ]
  }
}
```

The fields are:

* `findings`
* `previous_tests`
* `available_tests`
* `retrieved_knowledge`
* `chain_state`

P2 does not rename or add fields to the shared planner input contract.

### 4.2 Planner interface

The current P2 integration calls:

```text
AdaptivePlanner.plan(planner_input)
```

The P3 planner owns:

* RAG/security knowledge retrieval
* scoring
* LLM decision generation
* decision validation
* deterministic fallback behavior

P2 owns:

* experiment state
* experiment ID
* previous/executed tests
* available test state
* persistence of findings and logs
* orchestration around planner and sandbox calls

### 4.3 Planner response

Expected `PlannerDecision` JSON shape:

```json
{
  "selected_test": "tool_access_test",
  "reason": "This test is relevant to the current finding and has not been executed.",
  "priority": 0.8,
  "confidence": 0.9
}
```

The planner response fields are:

* `selected_test`
* `reason`
* `priority`
* `confidence`

P2 does not rename or modify these fields.

Important:

* The P3 planner and its LLM/RAG/scoring logic remain in the separate AI engine component.
* `/ai/plan` remains a documented integration contract rather than a separate FastAPI endpoint.
* The direct Python interface is the current integration mechanism.

---

## 5. Sandbox integration contract

Status: Integration contract.

The backend does not currently expose `/sandbox/test` as a separate FastAPI endpoint. P2 currently integrates with the P4 sandbox through its Python interface.

### 5.1 Sandbox interface

The current P2 orchestration calls the P4 sandbox executor with:

```text
execute_sandbox_test(experiment_id, test_name)
```

Current supported test names:

* `permission_test`
* `tool_access_test`
* `memory_access_test`

Expected sandbox response shape:

```json
{
  "status": "completed",
  "test": "permission_test",
  "finding": "weak_permission_control",
  "severity": "high",
  "evidence": {
    "permission": "DENIED",
    "observed_behavior": "TOOL_ALLOWED"
  },
  "confidence": 1.0
}
```

The P2 backend stores the returned finding and associated evidence in the MongoDB `findings` collection.

### 5.2 Sandbox validation

The P2 backend integrates with the P4 validator through:

```text
ChainValidator(experiment_id)
```

and:

```text
validate_chain(chain_id, executed_tests)
```

The validator checks:

* expected finding
* evidence
* dependency order
* step validity

The current dependency order is:

```text
permission_test
    ↓
tool_access_test
    ↓
memory_access_test
```

Important:

* Sandbox execution and validation logic remain owned by P4.
* P2 does not create or modify sandbox vulnerabilities.
* `/sandbox/test` remains a documented integration contract rather than a separate FastAPI endpoint.
* The current backend uses the existing P4 Python interfaces directly.

---

## 6. Current implementation status summary

Implemented in backend:

* `/health`
* `/experiments`
* `/experiments/{experiment_id}`
* `/experiments/{experiment_id}/logs`
* `/experiments/{experiment_id}/findings`
* `/experiments/{experiment_id}/chains`
* `/experiments/{experiment_id}/start`
* `/experiments/{experiment_id}/status`
* `/chains/{chain_id}/validate`
* `/analytics`

Current internal integrations:

* P3 `AdaptivePlanner.plan(...)`
* P3 `PlannerInput`
* P3 `PlannerDecision`
* P4 `execute_sandbox_test(...)`
* P4 `ChainValidator`

Not exposed as separate FastAPI endpoints:

* `/ai/plan`
* `/sandbox/test`

These remain documented integration contracts for the separate AI planner and sandbox modules.

The current P2 backend acts as the central orchestration layer between the frontend, MongoDB, P3 AI planner, and P4 sandbox/validator.

---

## 7. Phase 2 mitigation API contracts

Status: Planned Phase 2 API contract. These endpoints are documented for the
Phase 2 workflow but are not implemented as FastAPI routes yet.

Phase 2 introduces a separate defensive-control selection contract. It does
not change the Phase 1 test-selection contract:

```text
PlannerInput
    → AdaptivePlanner.plan()
    → PlannerDecision
    → selected_test
    → execute_sandbox_test()
```

The only allowed defensive-control values are:

* `authorization_gate`
* `tool_allowlist`
* `memory_validation`

The LLM may select only one of these predefined controls. It must not produce
arbitrary patches, modify source code, deploy code, or perform autonomous code
changes.

### 7.1 POST /experiments/{experiment_id}/mitigation/select

Requests selection of a predefined defensive control using finding and
attack-chain context.

Request:
- Method: POST
- Path: `/experiments/{experiment_id}/mitigation/select`
- Body: `MitigationSelectionRequest`

Request JSON:

```json
{
  "chain_id": "CHAIN-d4f70fa4",
  "finding": "unsafe_tool_access",
  "severity": "high",
  "evidence": {
    "expected": "Tool should not be exposed.",
    "actual": "Tool was exposed to the agent."
  },
  "attack_chain": [
    "permission_test",
    "tool_access_test"
  ],
  "chain_context": {
    "validated_steps": 2,
    "current_stage": "mitigation_selection"
  }
}
```

Important request fields:

* `chain_id`: non-empty attack-chain identifier.
* `finding`: finding being mitigated.
* `severity`: finding severity.
* `evidence`: finding evidence; the schema permits structured or scalar data.
* `attack_chain`: one or more existing Phase 1 test names in chain order.
* `chain_context`: additional chain-analysis context.

The experiment identity is taken exclusively from the
`{experiment_id}` path parameter.

Response: `MitigationSelectionResponse`

```json
{
  "mitigation_run_id": "MIT-001",
  "selected_control": "tool_allowlist",
  "reason": "The finding shows that a restricted tool was exposed.",
  "confidence": 0.92
}
```

The `selected_control` value must be exactly one of:

* `authorization_gate`
* `tool_allowlist`
* `memory_validation`

Expected errors:

* HTTP 404 if the experiment or chain does not exist.
* HTTP 422 for malformed request fields or an unsupported control value.
* HTTP 409 if the chain is not eligible for mitigation selection.

### 7.2 POST /experiments/{experiment_id}/mitigation/apply

Applies the already-selected predefined defensive control. This endpoint does
not select a new control and does not accept arbitrary patch instructions.

Request:
- Method: POST
- Path: `/experiments/{experiment_id}/mitigation/apply`
- Body: `MitigationApplyRequest`

Request JSON:

```json
{
  "mitigation_run_id": "MIT-001",
  "selected_control": "tool_allowlist"
}
```

The `mitigation_run_id` must identify the run created by the selection
endpoint. The selected value must be one of `authorization_gate`,
`tool_allowlist`, or `memory_validation`.

Response: `ControlApplicationResult`

```json
{
  "selected_control": "tool_allowlist",
  "status": "applied",
  "execution_info": {
    "control_id": "tool_allowlist",
    "applied_to": "CHAIN-d4f70fa4"
  }
}
```

Response fields:

* `selected_control`: the approved control that was applied.
* `status`: application status such as `applied` or `failed`.
* `execution_info`: structured information about the controlled application.

Expected errors:

* HTTP 404 if the experiment or selected mitigation run does not exist.
* HTTP 422 for an unsupported control value.
* HTTP 409 if no control has been selected, the control was already applied,
  or the experiment is not ready for application.
* HTTP 500 or a structured failure response if controlled application fails.

### 7.3 POST /experiments/{experiment_id}/mitigation/replay

Replays the same attack/test after the defensive control has been applied.
The replay must use the attack/test represented by the original before result;
it is not a new attack selection and must not invoke the Phase 1 planner to
choose a different test.

Request:
- Method: POST
- Path: `/experiments/{experiment_id}/mitigation/replay`
- Body: `MitigationReplayRequest`

Request JSON:

```json
{
  "mitigation_run_id": "MIT-001",
  "test": "tool_access_test"
}
```

The `mitigation_run_id` must identify the run whose control application has
completed. `chain_id` is not required in this request because it is already
associated with the mitigation run.

Response: `BeforeAfterReplayResult`

```json
{
  "test": "tool_access_test",
  "before_result": {
    "status": "completed",
    "finding": "unsafe_tool_access",
    "evidence": {
      "actual": "Tool was exposed to the agent."
    }
  },
  "after_result": {
    "status": "completed",
    "finding": null,
    "evidence": {
      "actual": "Tool access was blocked by the allowlist."
    }
  },
  "blocked_after_mitigation": true
}
```

Response fields:

* `test`: the exact Phase 1 attack/test identity replayed.
* `before_result`: the original result for that same attack/test.
* `after_result`: the result from replaying that same attack/test after
  mitigation.
* `blocked_after_mitigation`: whether the attack was blocked after control
  application.

Expected errors:

* HTTP 404 if the experiment or original replay result does not exist.
* HTTP 409 if the selected control has not been applied or the replay test
  does not match the original before-result test.
* HTTP 422 for an invalid or missing test identity.

### 7.4 GET /experiments/{experiment_id}/mitigation/result

Retrieves the completed mitigation and chain-disruption result for an
experiment.

Request:
- Method: GET
- Path: `/experiments/{experiment_id}/mitigation/result?mitigation_run_id=MIT-001`
- Body: none

The `mitigation_run_id` query parameter identifies the run created by the
selection endpoint. It must belong to the experiment in the path.

Response: `MitigationResultResponse`

```json
{
  "mitigation_run_id": "MIT-001",
  "experiment_id": "EXP001",
  "chain_id": "CHAIN-d4f70fa4",
  "status": "completed",
  "selection": {
    "mitigation_run_id": "MIT-001",
    "selected_control": "tool_allowlist",
    "reason": "The finding shows that a restricted tool was exposed.",
    "confidence": 0.92
  },
  "application": {
    "selected_control": "tool_allowlist",
    "status": "applied",
    "execution_info": {
      "control_id": "tool_allowlist"
    }
  },
  "replay": {
    "test": "tool_access_test",
    "before_result": {
      "status": "completed",
      "finding": "unsafe_tool_access"
    },
    "after_result": {
      "status": "completed",
      "finding": null
    },
    "blocked_after_mitigation": true
  },
  "disruption": {
    "before_validation": {
      "status": "validated",
      "validated_steps": 2,
      "total_steps": 2
    },
    "after_validation": {
      "status": "invalid",
      "validated_steps": 1,
      "total_steps": 2
    },
    "disrupted": true,
    "residual_vulnerable_steps": [
      "permission_test"
    ],
    "validation_result": {
      "blocked_steps": [
        "tool_access_test"
      ],
      "all_findings_reproduced": false
    }
  }
}
```

Response fields:

* `mitigation_run_id`: the mitigation workflow identity returned by selection.
* `experiment_id`: the experiment associated with the mitigation run.
* `chain_id`: the analyzed attack-chain identifier.
* `status`: the mitigation workflow status.
* `selection`: the `MitigationSelectionResponse` for this run.
* `application`: the `ControlApplicationResult` for this run.
* `replay`: the `BeforeAfterReplayResult` for this run.
* `disruption`: the `ChainDisruptionResult` for this run.
* `disruption.before_validation`: validation information before mitigation.
* `disruption.after_validation`: validation information after mitigation and
  same-chain replay.
* `disruption.disrupted`: whether the defensive control disrupted the chain.
* `disruption.residual_vulnerable_steps`: steps that remain vulnerable after
  mitigation.
* `disruption.validation_result`: additional structured before/after
  validation details.

Expected errors:

* HTTP 404 if the experiment or mitigation result does not exist.
* HTTP 409 if the mitigation run does not belong to the experiment, mitigation
  has not completed, or same-attack replay is pending.

### 7.5 Phase 2 ownership and flow

The Phase 2 experiment-level workflow is:

```text
Attack-Chain Discovery
    → Attack-Chain Analysis
    → LLM + Security RAG
    → Select Predefined Defensive Control
    → Apply Control
    → Replay SAME Attack
    → Before/After Validation
    → Chain Disruption Report
```

The workflow identity is carried through the endpoints as follows:

```text
POST .../mitigation/select
    → returns mitigation_run_id
POST .../mitigation/apply
    → submits mitigation_run_id
POST .../mitigation/replay
    → submits mitigation_run_id
GET .../mitigation/result?mitigation_run_id=...
    → retrieves the same mitigation run
```

P2 owns:

* the experiment-level API endpoints documented in this section
* orchestration between P3 and P4
* experiment, chain, mitigation, replay, and disruption state
* persistence of the resulting records

P3 owns:

* selecting exactly one approved defensive control using LLM + Security RAG
* returning the control selection rationale and confidence

P4 owns:

* applying the predefined defensive control in the controlled environment
* replaying the same attack/test
* performing before/after validation
* reporting whether the chain was disrupted and which steps remain vulnerable

These are internal P2-to-P3 and P2-to-P4 integration boundaries. Phase 2
does not introduce public `/ai/mitigation` or `/sandbox/mitigation` routes.
