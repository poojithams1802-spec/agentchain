# AgentChain API Contract

This document describes the backend API contract implemented in the current FastAPI service and the integration contracts planned for the AI planner and sandbox modules.

Status legend:
- Implemented: live FastAPI endpoint in the current backend
- Integration contract: contract expected for future P3/P4 integration; not implemented in the backend yet

---

## 1. Experiment lifecycle statuses

The current experiment lifecycle in the backend is intentionally simple and beginner-friendly.

- `created`: experiment has been created but not started
- `running`: experiment is currently active
- `completed`: mock orchestration flow has finished

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
```

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
- `name`: string, minimum length 1
- `mode`: string, minimum length 1
- `max_tests`: integer greater than 0

Response JSON:
```json
{
  "experiment_id": "EXP001",
  "status": "created"
}
```

Notes:
- `experiment_id` is generated as `EXP` + a zero-padded numeric counter.
- The new document is stored in the MongoDB `experiments` collection.

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
- HTTP 404
- body: `{"detail": "Experiment not found"}`

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

If the experiment does not exist:
- HTTP 404
- body: `{"detail": "Experiment not found"}`

---

### 2.6 GET /experiments/{experiment_id}/findings

Returns findings for an experiment from the MongoDB `findings` collection.

Response JSON:
```json
[
  {
    "experiment_id": "EXP001",
    "test": "tool_access_test",
    "finding": "Mock finding from sandbox",
    "severity": "medium",
    "evidence": "Mock evidence for orchestration testing",
    "timestamp": "2026-09-25T12:34:56.789012+00:00"
  }
]
```

If the experiment does not exist:
- HTTP 404
- body: `{"detail": "Experiment not found"}`

---

### 2.7 GET /experiments/{experiment_id}/chains

Returns attack-chain records for an experiment from the MongoDB `attack_chains` collection.

Response JSON:
```json
[
  {
    "experiment_id": "EXP001",
    "name": "example_chain",
    "steps": ["step_1", "step_2"],
    "timestamp": "2026-09-25T12:34:56.789012+00:00"
  }
]
```

If the experiment does not exist:
- HTTP 404
- body: `{"detail": "Experiment not found"}`

---

### 2.8 POST /experiments/{experiment_id}/start

This endpoint is a mock orchestration skeleton for the current backend phase.

Behavior:
1. Verify the experiment exists.
2. Update the experiment status to `running`.
3. Insert a log: `"Experiment started"`.
4. Execute a mock test: `"tool_access_test"`.
5. Create a mock finding using the existing helper with:
   - `test`: `tool_access_test`
   - `finding`: `Mock finding from sandbox`
   - `severity`: `medium`
   - `evidence`: `Mock evidence for orchestration testing`
6. Insert a log: `"Mock test executed: tool_access_test"`.
7. Update the experiment status to `completed`.
8. Insert a log: `"Experiment completed"`.

Response JSON:
```json
{
  "experiment_id": "EXP001",
  "status": "completed",
  "executed_tests": ["tool_access_test"],
  "findings_created": 1
}
```

If the experiment does not exist:
- HTTP 404
- body: `{"detail": "Experiment not found"}`

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
- HTTP 404
- body: `{"detail": "Experiment not found"}`

---

### 2.10 POST /chains/{chain_id}/validate

Simple validation stub for a stored attack chain.

Behavior:
- Checks whether the chain exists in the MongoDB `attack_chains` collection.
- Returns HTTP 404 if it does not exist.
- Otherwise returns a simple validation payload using the stored chain steps.

Response JSON:
```json
{
  "chain_id": "CHAIN001",
  "status": "validated",
  "validated_steps": ["step_1", "step_2"]
}
```

This is a backend skeleton only; it does not perform real security validation logic.

---

### 2.11 GET /analytics

Returns a minimal aggregate summary based directly on the existing MongoDB collections.

Response JSON:
```json
{
  "total_experiments": 5,
  "total_findings": 3,
  "total_chains": 2
}
```

This endpoint only includes metrics that can be counted directly from the existing collections.

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
  "test": "tool_access_test",
  "finding": "Mock finding from sandbox",
  "severity": "medium",
  "evidence": "Mock evidence for orchestration testing",
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
  "experiment_id": "EXP001",
  "name": "example_chain",
  "steps": ["step_1", "step_2"],
  "timestamp": "2026-09-25T12:34:56.789012+00:00"
}
```

---

## 4. AI planner integration contract (not implemented yet)

Status: Integration contract only.

The backend does not currently expose this endpoint. It is documented here to match the AI planner design in the project implementation specification.

### 4.1 POST /ai/plan

Request JSON shape:
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
  "previous_tests": ["permission_test"],
  "available_tests": ["tool_access_test", "file_access_test"],
  "retrieved_knowledge": ["Least privilege policy", "File access restrictions"],
  "chain_state": {
    "current_step": 2,
    "risk_level": "medium"
  }
}
```

This matches the `PlannerInput` model used by the AI planner module.

Expected response JSON shape:
```json
{
  "selected_test": "tool_access_test",
  "reason": "This test is relevant to the current finding and not previously executed.",
  "priority": 0.8,
  "confidence": 0.9
}
```

This matches the `PlannerDecision` model used by the AI planner module.

Important:
- This endpoint is an integration contract only.
- It is not implemented in the FastAPI backend yet.
- The AI planner and its LLM/retrieval logic remain in the separate AI engine component.

---

## 5. Sandbox integration contract (not implemented yet)

Status: Integration contract only.

The backend does not currently expose this endpoint. It is documented here based on the project security sandbox design and the existing finding helper model.

### 5.1 POST /sandbox/test

Request JSON shape (expected integration contract):
```json
{
  "experiment_id": "EXP001",
  "test": "tool_access_test",
  "context": {
    "allowed_tools": ["search", "memory"],
    "permissions": {
      "search": true,
      "file": false
    }
  }
}
```

Expected response JSON shape:
```json
{
  "experiment_id": "EXP001",
  "test": "tool_access_test",
  "status": "completed",
  "finding": "Mock finding from sandbox",
  "severity": "medium",
  "confidence": 0.8,
  "evidence": "Mock evidence for orchestration testing"
}
```

Important:
- This endpoint is an integration contract only.
- It is not implemented in the FastAPI backend yet.
- It is expected to run sandbox logic separately from the API layer and return a structured finding payload similar to the current finding model.

---

## 6. Current implementation status summary

Implemented in backend:
- `/health`
- `/experiments`
- `/experiments/{experiment_id}`
- `/experiments/{experiment_id}/logs`
- `/experiments/{experiment_id}/findings`
- `/experiments/{experiment_id}/chains`
- `/experiments/{experiment_id}/start`
- `/experiments/{experiment_id}/status`
- `/chains/{chain_id}/validate`
- `/analytics`

Not implemented yet in backend:
- `/ai/plan`
- `/sandbox/test`

Both are documented here as integration contracts for future P3/P4 work.
