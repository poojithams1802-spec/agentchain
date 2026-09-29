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
