# AgentChain Architecture Documentation

## 1. System Architecture

AgentChain is a controlled research platform for discovering multi-step attack chains in intentionally vulnerable agentic AI systems.

The system follows a modular architecture in which the React frontend communicates with the FastAPI backend. The backend acts as the central orchestration layer and coordinates the AI planner, controlled sandbox, chain validator, and MongoDB database.

### High-Level Architecture

```text
                    ┌─────────────────────┐
                    │   React Frontend    │
                    │                     │
                    │ Dashboard            │
                    │ Experiments          │
                    │ Live Logs            │
                    │ Findings             │
                    │ Attack Chains        │
                    │ Analytics            │
                    └──────────┬──────────┘
                               │
                         HTTP / REST API
                               │
                               ▼
                    ┌─────────────────────┐
                    │   FastAPI Backend   │
                    │       (P2)          │
                    │                     │
                    │ Experiment APIs      │
                    │ Orchestration        │
                    │ State Management     │
                    │ Persistence          │
                    └──────┬──────┬───────┘
                           │      │
                 ┌─────────┘      └─────────┐
                 ▼                          ▼
        ┌─────────────────┐        ┌─────────────────┐
        │   AI Engine     │        │ Controlled      │
        │      (P3)       │        │ Sandbox (P4)    │
        │                 │        │                 │
        │ RAG Retrieval   │        │ Test Execution  │
        │ Planner         │        │ Findings        │
        │ Scoring         │        │ Validation      │
        │ LLM Decision    │        │                 │
        └─────────────────┘        └─────────────────┘
                 │                          │
                 └──────────┬───────────────┘
                            │
                            ▼
                    ┌─────────────────────┐
                    │       MongoDB       │
                    │                     │
                    │ Experiments         │
                    │ Findings            │
                    │ Logs                │
                    │ Attack Chains       │
                    │ Evaluation Results  │
                    └─────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| React Frontend (P1) | Provides the user interface for experiments, logs, findings, attack chains, and analytics |
| FastAPI Backend (P2) | Acts as the central integration and orchestration layer |
| AI Engine (P3) | Performs security knowledge retrieval, adaptive planning, scoring, LLM decision generation, and planner validation |
| Controlled Sandbox (P4) | Executes controlled security tests against the intentionally vulnerable agent environment |
| Chain Validator (P4) | Replays and validates candidate attack chains, including findings, evidence, dependencies, and step validity |
| MongoDB | Persists experiment state, findings, logs, attack chains, and evaluation results |

### Architectural Principle

The FastAPI backend is the central layer between the frontend, AI engine, sandbox, and database.

The frontend does not directly access MongoDB. P2 owns experiment state, persistence, and orchestration, while P3 owns adaptive planning and P4 owns sandbox execution and chain validation.

---

## 2. P2 Backend Architecture

The P2 backend is implemented using FastAPI and acts as the central orchestration layer of AgentChain.

Its main responsibilities are:

- Managing the experiment lifecycle
- Maintaining experiment state
- Coordinating the adaptive planner and sandbox
- Persisting findings, logs, chains, and evaluation results
- Providing REST APIs to the frontend
- Triggering candidate-chain validation
- Providing aggregate analytics

### Backend Structure

The backend is organized around the FastAPI application and supporting modules:

```text
backend/
├── app/
│   ├── main.py
│   ├── database.py
│   └── schemas.py
├── .env
└── requirements.txt
```

### Main Backend Components

#### FastAPI Application

`app/main.py` contains the API endpoints and the experiment orchestration logic.

It handles requests from the frontend and coordinates calls to the AI planner and controlled sandbox.

#### Database Layer

`app/database.py` establishes the MongoDB connection using the configured environment variables.

The backend uses MongoDB to persist experiment and evaluation data.

#### Pydantic Schemas

`app/schemas.py` contains the Pydantic models used to validate structured API input and shared experiment data.

### Experiment State Management

Each experiment follows the following lifecycle:

```text
created
   │
   ▼
running
   │
   ▼
completed
```

- `created` — experiment has been created but has not started.
- `running` — experiment execution is currently active.
- `completed` — experiment execution and the current orchestration and validation flow have finished.

The experiment state is stored in the MongoDB `experiments` collection.

### Backend Responsibility Boundary

P2 is responsible for coordinating the system but does not own the internal AI planning or sandbox logic.

```text
P2
│
├── Experiment state
├── Experiment ID
├── Previous/executed tests
├── Available test state
├── Findings persistence
├── Logs persistence
└── Orchestration
      │
      ├── P3 → Adaptive planning
      │
      └── P4 → Sandbox execution and validation
```

The P3 planner retains ownership of RAG retrieval, scoring, LLM decision generation, decision validation, and fallback behavior. P4 retains ownership of sandbox execution and chain validation.

## 3. Experiment Orchestration Flow

The experiment orchestration is handled by the P2 FastAPI backend. When an experiment is started, the backend coordinates the adaptive planner, sandbox execution, persistence, candidate-chain creation, and validation.

### Experiment Execution Flow

```text
Create Experiment
       │
       ▼
Set Status = Running
       │
       ▼
Build Planner Input
       │
       ▼
P3 Adaptive Planner
       │
       ▼
Select Next Test
       │
       ▼
P4 Sandbox Execution
       │
       ▼
Store Finding + Evidence
       │
       ▼
Update Experiment State
       │
       ▼
More Tests Available?
      / \
    Yes  No
     │    │
     │    ▼
     │  Create Candidate Chain
     │    │
     │    ▼
     │  P4 Chain Validator
     │    │
     │    ▼
     │  Store Evaluation Result
     │    │
     └────┘
       │
       ▼
Set Status = Completed
```

### Detailed Orchestration Steps

When `POST /experiments/{experiment_id}/start` is called, the backend performs the following sequence:

1. Verifies that the experiment exists.
2. Updates the experiment status to `running`.
3. Creates an experiment-start log entry.
4. Builds the planner input using the current findings and execution state.
5. Calls the P3 adaptive planner through its Python interface.
6. Receives the planner decision containing the selected test.
7. Executes the selected test through the P4 sandbox executor.
8. Stores the resulting finding, severity, evidence, and confidence.
9. Stores orchestration logs for the execution.
10. Updates the list of previously executed and available tests.
11. Repeats the planning and execution cycle until the test budget is reached or no further test can be selected.
12. Creates a candidate attack chain from the executed test sequence.
13. Sends the candidate chain to the P4 `ChainValidator`.
14. Stores the validation result in the MongoDB `evaluation_results` collection.
15. Updates the experiment status to `completed`.

### Adaptive Planning State

For each planning iteration, P2 maintains the execution state required by the P3 planner:

```text
Findings
    +
Previous Tests
    +
Available Tests
    +
Retrieved Knowledge
    +
Chain State
    │
    ▼
PlannerInput
    │
    ▼
AdaptivePlanner.plan()
    │
    ▼
PlannerDecision
    │
    ├── selected_test
    ├── reason
    ├── priority
    └── confidence
```

The backend does not modify the planner's decision schema. The P3 planner remains responsible for RAG retrieval, scoring, LLM decision generation, decision validation, and fallback behavior.

### Sandbox Execution

The selected test is passed to the P4 sandbox using:

```text
execute_sandbox_test(experiment_id, test_name)
```

The current supported tests are:

```text
permission_test
tool_access_test
memory_access_test
```

The sandbox returns structured information containing the test status, finding, severity, evidence, and confidence.

P2 stores the resulting finding and associated evidence in MongoDB.

### Candidate Chain and Validation

After the execution loop finishes, P2 creates a candidate attack chain using the sequence of executed tests.

The candidate chain is then passed to the P4 validator:

```text
ChainValidator(experiment_id)
        │
        ▼
validate_chain(chain_id, executed_tests)
```

The validator checks:

- Expected finding
- Evidence existence
- Dependency order
- Step validity

The resulting validation record is stored in the `evaluation_results` collection.

### End-to-End Flow

The complete AgentChain execution path is:

```text
Frontend
   │
   ▼
FastAPI Backend
   │
   ├──────────────► P3 Adaptive Planner
   │                       │
   │                       ▼
   │                 Selected Test
   │                       │
   └───────────────────────┼──────────────► P4 Sandbox
                           │                       │
                           │                       ▼
                           │                  Finding + Evidence
                           │                       │
                           ◄───────────────────────┘
   │
   ▼
MongoDB Persistence
   │
   ▼
Candidate Attack Chain
   │
   ▼
P4 Chain Validator
   │
   ▼
Evaluation Result
   │
   ▼
Frontend Dashboard
```

## 4. MongoDB Data Architecture

MongoDB is used as the persistent storage layer for AgentChain.

The P2 backend manages the database connection and stores experiment state, findings, orchestration logs, candidate attack chains, and chain-validation results.

### Database Collections

The backend uses the following MongoDB collections:

| Collection | Purpose |
|---|---|
| `experiments` | Stores experiment configuration and lifecycle status |
| `findings` | Stores findings produced by sandbox test execution |
| `experiment_logs` | Stores experiment execution and orchestration logs |
| `attack_chains` | Stores candidate attack chains and their executed test steps |
| `evaluation_results` | Stores chain-validation and evaluation results |
| `knowledge_documents` | Stores knowledge-base documents used by the AgentChain system |

### Collection Relationships

```text
                    ┌──────────────────┐
                    │    experiments   │
                    │                  │
                    │ experiment_id    │
                    │ name             │
                    │ mode             │
                    │ max_tests        │
                    │ status           │
                    └────────┬─────────┘
                             │
             ┌───────────────┼────────────────┐
             │               │                │
             ▼               ▼                ▼
      ┌────────────┐  ┌──────────────┐  ┌──────────────┐
      │  findings  │  │ experiment_  │  │ attack_chains│
      │            │  │    logs      │  │              │
      │ Findings   │  │              │  │ Chain steps  │
      │ Evidence   │  │ Execution    │  │ Chain ID     │
      │ Severity   │  │ events       │  │ Experiment ID│
      └────────────┘  └──────────────┘  └──────┬───────┘
                                                │
                                                ▼
                                      ┌──────────────────┐
                                      │ evaluation_      │
                                      │    results       │
                                      │                  │
                                      │ Validation       │
                                      │ Chain status     │
                                      │ Validated steps  │
                                      │ Validation rate  │
                                      └──────────────────┘
```

### Experiment Record

The `experiments` collection stores the configuration and current state of each experiment.

```json
{
  "experiment_id": "EXP001",
  "name": "Experiment 001",
  "mode": "adaptive",
  "max_tests": 10,
  "status": "created"
}
```

### Finding Record

The `findings` collection stores the result of each sandbox test.

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

### Experiment Log Record

The `experiment_logs` collection stores important events during experiment execution.

```json
{
  "experiment_id": "EXP001",
  "message": "Experiment started",
  "timestamp": "2026-09-25T12:34:56.789012+00:00"
}
```

Examples of recorded events include:

- Experiment started
- Planner selected test
- Sandbox completed
- Candidate chain created
- Chain validation completed
- Experiment completed

### Attack Chain Record

The `attack_chains` collection stores candidate attack chains generated from the executed test sequence.

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

The `chain_id` is a stable string identifier generated when the candidate chain is created.

### Evaluation Result Record

The `evaluation_results` collection stores the result of candidate-chain validation.

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

The evaluation result allows the frontend and research evaluation components to access the outcome of chain validation without directly accessing the sandbox.

### Data Persistence Flow

```text
Experiment Created
       │
       ▼
experiments
       │
       ▼
Sandbox Test
       │
       ├──────────────► findings
       │
       └──────────────► experiment_logs
       │
       ▼
Candidate Chain
       │
       ▼
attack_chains
       │
       ▼
Chain Validation
       │
       ▼
evaluation_results
```

The frontend accesses this information through the FastAPI backend rather than directly accessing MongoDB.

## 5. P2 ↔ P3 and P2 ↔ P4 Integration Contracts

AgentChain uses clearly defined interfaces between the P2 backend, P3 AI engine, and P4 controlled sandbox.

P2 acts as the integration layer and passes structured data between these components without taking ownership of their internal implementation.

### P2 ↔ P3 Integration

The P2 backend calls the P3 adaptive planner through its Python interface:

```text
AdaptivePlanner.plan(planner_input)
```

P2 constructs the planner input using the current experiment state.

The planner input contains:

```text
PlannerInput
├── findings
├── previous_tests
├── available_tests
├── retrieved_knowledge
└── chain_state
```

The P3 planner returns a structured `PlannerDecision`:

```text
PlannerDecision
├── selected_test
├── reason
├── priority
└── confidence
```

### P2 Responsibilities

P2 is responsible for:

- Maintaining experiment state
- Maintaining the experiment ID
- Tracking previously executed tests
- Tracking available tests
- Providing current findings to the planner
- Calling the planner
- Using the planner's selected test for the next execution step
- Persisting the resulting data

### P3 Responsibilities

P3 is responsible for:

- Security knowledge retrieval
- RAG processing
- Planner scoring
- LLM-based decision generation
- Planner decision validation
- Fallback behavior

P2 does not modify the planner's internal decision logic or schema.

### P2 ↔ P3 Flow

```text
P2 Backend
    │
    │ PlannerInput
    ▼
AdaptivePlanner
    │
    ├── RAG Retrieval
    ├── Scoring
    ├── LLM Decision
    └── Decision Validation
    │
    │ PlannerDecision
    ▼
P2 Backend
```

---

### P2 ↔ P4 Integration

The P2 backend calls the controlled sandbox using:

```text
execute_sandbox_test(experiment_id, test_name)
```

The currently supported sandbox tests are:

```text
permission_test
tool_access_test
memory_access_test
```

The sandbox returns structured execution information:

```text
Sandbox Result
├── status
├── test
├── finding
├── severity
├── evidence
└── confidence
```

P2 stores the returned finding and execution information in MongoDB.

### P4 Responsibilities

P4 is responsible for:

- Controlled sandbox test execution
- Generating controlled findings
- Providing evidence
- Chain validation
- Checking finding correctness
- Checking evidence existence
- Checking dependency validity
- Checking overall chain validity

P2 does not implement the internal sandbox or validation logic.

### P2 ↔ P4 Flow

```text
P2 Backend
    │
    │ experiment_id + test_name
    ▼
Controlled Sandbox
    │
    ├── Execute Test
    ├── Generate Finding
    └── Collect Evidence
    │
    │ Sandbox Result
    ▼
P2 Backend
    │
    ▼
MongoDB
```

### Candidate Chain Validation

After the execution loop, P2 creates a candidate attack chain and passes it to the P4 validator:

```text
ChainValidator(experiment_id)
        │
        ▼
validate_chain(chain_id, executed_tests)
```

The validator checks the candidate chain and returns structured validation results.

```text
Candidate Chain
      │
      ▼
P4 Chain Validator
      │
      ├── Finding Match
      ├── Evidence Exists
      ├── Dependency Valid
      └── Step Valid
      │
      ▼
Validation Result
      │
      ▼
P2 → MongoDB
```

### Integration Boundary

The ownership boundaries between the components are:

| Area | P2 | P3 | P4 |
|---|---|---|---|
| Experiment lifecycle | ✓ | | |
| Experiment state | ✓ | | |
| Experiment ID | ✓ | | |
| Test execution state | ✓ | | |
| RAG retrieval | | ✓ | |
| Planner scoring | | ✓ | |
| LLM decision | | ✓ | |
| Planner validation | | ✓ | |
| Sandbox execution | | | ✓ |
| Finding generation | | | ✓ |
| Evidence generation | | | ✓ |
| Candidate chain creation | ✓ | | |
| Chain validation | | | ✓ |
| MongoDB persistence | ✓ | | |
| API/frontend integration | ✓ | | |

This separation allows each component to evolve independently while maintaining a stable integration contract.

## 6. API Architecture

The FastAPI backend exposes REST APIs that allow the frontend to create and monitor experiments and access findings, attack chains, validation results, and analytics.

The APIs provide a stable interface between the React frontend and the backend orchestration layer.

### Experiment APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/experiments` | Create a new experiment |
| GET | `/experiments` | List experiments |
| GET | `/experiments/{experiment_id}` | Retrieve a specific experiment |
| POST | `/experiments/{experiment_id}/start` | Start experiment execution |
| GET | `/experiments/{experiment_id}/status` | Retrieve experiment status |
| GET | `/experiments/{experiment_id}/logs` | Retrieve experiment logs |
| GET | `/experiments/{experiment_id}/findings` | Retrieve experiment findings |
| GET | `/experiments/{experiment_id}/chains` | Retrieve candidate attack chains |

### Chain and Validation APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/chains/{chain_id}/validate` | Validate a candidate attack chain |

### Analytics API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/analytics` | Retrieve aggregate experiment and evaluation metrics |

### Create Experiment

A new experiment is created using:

```http
POST /experiments
```

Example request:

```json
{
  "name": "Experiment 001",
  "mode": "adaptive",
  "max_tests": 10
}
```

The backend generates the experiment ID and returns the initial status.

Example response:

```json
{
  "experiment_id": "EXP001",
  "status": "created"
}
```

### Start Experiment

Experiment execution is started using:

```http
POST /experiments/{experiment_id}/start
```

This endpoint triggers the complete backend orchestration flow:

```text
Start Experiment
      │
      ▼
Planner
      │
      ▼
Sandbox
      │
      ▼
Finding
      │
      ▼
Next Test
      │
      ▼
Candidate Chain
      │
      ▼
Validation
      │
      ▼
Evaluation Result
```

### API Response Flow

The frontend obtains experiment information through the backend APIs.

```text
React Frontend
      │
      │ HTTP Request
      ▼
FastAPI Endpoint
      │
      ▼
Backend Logic
      │
      ▼
MongoDB
      │
      ▼
JSON Response
      │
      ▼
React Frontend
```

The frontend does not directly access MongoDB.

### API Documentation

FastAPI automatically provides interactive API documentation through Swagger UI.

The Swagger interface is available at:

```text
/docs
```

The OpenAPI specification is available at:

```text
/openapi.json
```

These interfaces allow the API endpoints and their request/response schemas to be inspected and tested independently of the React frontend.

## 7. End-to-End Integration Verification

The AgentChain backend was verified through an end-to-end integration test involving the frontend, FastAPI backend, AI planner, controlled sandbox, MongoDB persistence, and chain validator.

### Final E2E Experiment

The final integration experiment used:

```text
Experiment ID: EXP011
Mode: adaptive
Maximum tests: 3
```

The experiment successfully completed the following execution sequence:

```text
React Frontend
      │
      ▼
FastAPI Backend
      │
      ▼
P3 Adaptive Planner
      │
      ▼
P4 Controlled Sandbox
      │
      ▼
Finding Persistence
      │
      ▼
Candidate Attack Chain
      │
      ▼
P4 Chain Validator
      │
      ▼
MongoDB Evaluation Result
      │
      ▼
React Frontend
```

### Executed Tests

The final experiment executed three tests:

```text
1. permission_test
      ↓
   weak_permission_control

2. tool_access_test
      ↓
   unsafe_tool_access

3. memory_access_test
      ↓
   memory_validation_weakness
```

### Candidate Chain

The execution produced the candidate chain:

```text
CHAIN-83045c08
```

with the following steps:

```text
permission_test
      ↓
tool_access_test
      ↓
memory_access_test
```

### Validation Result

The candidate chain was successfully validated.

```text
Validated Steps:       3 / 3
Validation Rate:      100%
All Findings Reproduced: true
Evidence Available:    All Steps
Dependencies Valid:    All Steps
```

### Frontend Verification

The frontend integration was independently verified against the running FastAPI backend.

The following functionality was successfully verified:

- Experiments
- Experiment status
- Findings
- Logs
- Attack chains
- Chain validation
- Analytics

The final candidate chain was displayed in the frontend with all three steps validated.

No API contract mismatch was observed during the frontend end-to-end verification.

### Integration Outcome

The final integration demonstrated that the major AgentChain components can operate together through the defined interfaces:

```text
P1 Frontend
      ↕
P2 FastAPI Backend
      ↕
P3 Adaptive Planner
      ↕
P4 Controlled Sandbox
      ↕
P4 Chain Validator
      ↕
MongoDB
```

This verification confirmed the planned integration path from experiment creation through adaptive test execution, finding persistence, candidate-chain generation, validation, and frontend visualization.

## 8. Implementation Status and References

### Implementation Status

The P2 backend implementation and integration are complete for the current AgentChain development cycle.

The following P2 components have been implemented and verified:

- FastAPI backend
- MongoDB database integration
- Pydantic request and response schemas
- Experiment lifecycle management
- Experiment creation and retrieval APIs
- Experiment start and orchestration flow
- Experiment status tracking
- Experiment logs
- Finding persistence
- Candidate attack-chain persistence
- Chain validation integration
- Evaluation-result persistence
- Analytics API
- P3 adaptive planner integration
- P4 sandbox integration
- P4 chain-validator integration
- React frontend integration
- End-to-end experiment verification

### Integration Verification

The final end-to-end test confirmed the complete execution path:

```text
Experiment Creation
        ↓
Experiment Start
        ↓
Adaptive Planner
        ↓
Sandbox Test
        ↓
Finding Persistence
        ↓
Next Test Selection
        ↓
Candidate Chain
        ↓
Chain Validation
        ↓
Evaluation Result
        ↓
Frontend Visualization