from datetime import datetime, timezone
import os
import sys
import uuid

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from app.database import db
from app.schemas import (
    BeforeAfterReplayResult,
    ChainExecutionRequest,
    ChainExecutionResponse,
    ChainDisruptionResult,
    ControlApplicationResult,
    DefensiveControl,
    ExperimentCreate,
    MitigationApplyRequest,
    MitigationReplayRequest,
    MitigationResultResponse,
    MitigationSelectionRequest,
)
import app.mitigation_repository as mitigation_repository

# Load environment variables
load_dotenv("backend/.env")

# Make ai-engine and sandbox available
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)

sys.path.append(
    os.path.join(PROJECT_ROOT, "ai-engine")
)

sys.path.append(PROJECT_ROOT)

from planner import AdaptivePlanner
from schemas import PlannerInput, Finding
from mitigation_schemas import (
    MitigationFinding,
    MitigationSelectorInput,
)
from mitigation_selector import MitigationSelector
from sandbox.mitigation.mitigation_executor import apply_mitigation
from sandbox.mitigation.replay_executor import replay_attack
from sandbox.chains.chain_executor import (
    execute_chain,
    chain_result_to_research_result,
)
from sandbox.evaluation.mitigation_evaluation import (
    build_mitigation_experiment_record,
)
from sandbox.evaluation.phase2_runner import run_all_phase2_experiments
from sandbox.evaluation.phase2_metrics import calculate_phase2_metrics
from sandbox.evaluation.research_metrics import calculate_research_metrics
from sandbox.execution.sandbox_executor import execute_sandbox_test
from sandbox.validator.chain_validator import ChainValidator
from app.phase2_persistence import persist_phase2_condition_records
from app.phase3_persistence import persist_phase3_chain_result


app = FastAPI()

# Initialize P3 planner
planner = AdaptivePlanner()


def add_experiment_log(
    experiment_id: str,
    message: str
) -> None:

    log_entry = {
        "experiment_id": experiment_id,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    db.experiment_logs.insert_one(log_entry)


def add_experiment_finding(
    experiment_id: str,
    test: str,
    finding: str,
    severity: str,
    evidence,
    confidence: float,
) -> None:

    finding_entry = {
        "experiment_id": experiment_id,
        "test": test,
        "finding": finding,
        "severity": severity,
        "evidence": evidence,
        "confidence": confidence,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    db.findings.insert_one(finding_entry)


def add_attack_chain(
    experiment_id: str,
    name: str,
    steps: list[str],
) -> str:

    # Create our own readable string ID
    chain_id = f"CHAIN-{uuid.uuid4().hex[:8]}"

    chain_entry = {
        "chain_id": chain_id,
        "experiment_id": experiment_id,
        "name": name,
        "steps": steps,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    db.attack_chains.insert_one(chain_entry)

    return chain_id


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/experiments")
def create_experiment(payload: ExperimentCreate):

    experiment_count = db.experiments.count_documents({}) + 1

    experiment_id = f"EXP{experiment_count:03d}"

    experiment = {
        "experiment_id": experiment_id,
        "name": payload.name,
        "mode": payload.mode,
        "max_tests": payload.max_tests,
        "status": "created",
    }

    db.experiments.insert_one(experiment)

    return {
        "experiment_id": experiment_id,
        "status": "created",
    }


@app.get("/experiments")
def get_experiments():

    experiments = list(
        db.experiments.find({})
    )

    return [
        {
            "experiment_id": item["experiment_id"],
            "name": item["name"],
            "mode": item["mode"],
            "max_tests": item["max_tests"],
            "status": item["status"],
        }
        for item in experiments
    ]


@app.get("/experiments/{experiment_id}")
def get_experiment(
    experiment_id: str
):

    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    return {
        "experiment_id": experiment["experiment_id"],
        "name": experiment["name"],
        "mode": experiment["mode"],
        "max_tests": experiment["max_tests"],
        "status": experiment["status"],
    }


@app.get("/experiments/{experiment_id}/logs")
def get_experiment_logs(
    experiment_id: str
):

    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    logs = list(
        db.experiment_logs.find(
            {"experiment_id": experiment_id},
            {"_id": 0},
        )
    )

    return logs


@app.get("/experiments/{experiment_id}/findings")
def get_experiment_findings(
    experiment_id: str
):

    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    findings = list(
        db.findings.find(
            {"experiment_id": experiment_id},
            {"_id": 0},
        )
    )

    return findings


@app.get("/experiments/{experiment_id}/chains")
def get_experiment_chains(
    experiment_id: str
):

    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    chains = list(
        db.attack_chains.find(
            {"experiment_id": experiment_id},
            {"_id": 0},
        )
    )

    return chains


@app.post(
    "/experiments/{experiment_id}/chains/execute",
    response_model=ChainExecutionResponse,
)
def execute_experiment_chain(
    experiment_id: str,
    payload: ChainExecutionRequest,
):
    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    chain = db.attack_chains.find_one(
        {
            "chain_id": payload.chain_id,
            "experiment_id": experiment_id,
        }
    )

    if chain is None:
        raise HTTPException(
            status_code=404,
            detail="Chain not found",
        )

    result = execute_chain(experiment_id, payload.chain_id)

    if result.get("status") == "invalid":
        raise HTTPException(
            status_code=400,
            detail=result.get("error") or "Chain execution failed",
        )

    research_result = chain_result_to_research_result(
        result,
        mode=experiment.get("mode", "adaptive"),
        llm_calls=0,
        fallback_used=False,
    )
    persist_phase3_chain_result(research_result)

    return result


@app.post("/experiments/{experiment_id}/mitigation/select")
def select_mitigation(
    experiment_id: str,
    payload: MitigationSelectionRequest,
):

    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    chain = db.attack_chains.find_one(
        {
            "chain_id": payload.chain_id,
            "experiment_id": experiment_id,
        }
    )

    if chain is None:
        raise HTTPException(
            status_code=404,
            detail="Chain not found",
        )

    if payload.attack_chain != chain.get("steps"):
        raise HTTPException(
            status_code=409,
            detail="Attack chain does not match stored chain",
        )

    mitigation_run = (
        mitigation_repository.create_mitigation_run(
            experiment_id=experiment_id,
            chain_id=payload.chain_id,
            finding_context={
                "finding": payload.finding,
                "severity": payload.severity,
                "evidence": payload.evidence,
            },
            attack_chain_context={
                "steps": payload.attack_chain,
                "context": payload.chain_context,
            },
        )
    )

    selector_input = MitigationSelectorInput(
        findings=[
            MitigationFinding(
                finding=payload.finding,
                severity=payload.severity,
                confidence=0.0,
                evidence=str(payload.evidence),
            )
        ],
        attack_chain=payload.attack_chain,
        available_controls=[
            control.value
            for control in DefensiveControl
        ],
        chain_state=payload.chain_context,
        retrieved_knowledge=[],
    )

    try:
        selector = MitigationSelector()
        decision = selector.select(
            selector_input
        )
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Mitigation selector failed",
        ) from error

    selector_metrics = getattr(
        selector,
        "last_metrics",
        {},
    )
    if not isinstance(selector_metrics, dict):
        selector_metrics = {}

    try:
        selected_control = DefensiveControl(
            decision.selected_control
        )
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="Mitigation selector returned an invalid control",
        ) from error

    mitigation_repository.update_mitigation_run(
        mitigation_run["mitigation_run_id"],
        status="selected",
        selection={
            "selected_control": selected_control.value,
            "reason": decision.reason,
            "confidence": decision.confidence,
            "priority": decision.priority,
            "retrieved_knowledge": list(
                selector_input.retrieved_knowledge
            ),
            "llm_calls": int(
                bool(selector_metrics.get("llm_called"))
            ),
            "fallback_used": bool(
                selector_metrics.get("fallback_used", False)
            ),
        },
    )

    return {
        "mitigation_run_id": mitigation_run[
            "mitigation_run_id"
        ],
        "selected_control": selected_control.value,
        "reason": decision.reason,
        "confidence": decision.confidence,
    }


@app.post(
    "/experiments/{experiment_id}/mitigation/apply",
    response_model=ControlApplicationResult,
)
def apply_mitigation_to_run(
    experiment_id: str,
    payload: MitigationApplyRequest,
):
    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    mitigation_run = mitigation_repository.get_mitigation_run(
        payload.mitigation_run_id
    )

    if (
        mitigation_run is None
        or mitigation_run.get("experiment_id") != experiment_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Mitigation run not found",
        )

    selection = mitigation_run.get("selection")
    selected_control_value = (
        selection.get("selected_control")
        if isinstance(selection, dict)
        else None
    )

    if not selected_control_value:
        raise HTTPException(
            status_code=409,
            detail="Mitigation run has no selected control",
        )

    try:
        selected_control = DefensiveControl(selected_control_value)
        requested_control = DefensiveControl(payload.selected_control)
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=409,
            detail="Mitigation run has an invalid selected control",
        ) from error

    if requested_control != selected_control:
        raise HTTPException(
            status_code=409,
            detail="Selected control does not match mitigation run",
        )

    try:
        application_result = apply_mitigation(
            experiment_id,
            control_name=selected_control.value,
        )
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Mitigation application failed",
        ) from error

    if (
        not isinstance(application_result, dict)
        or application_result.get("status") != "applied"
    ):
        raise HTTPException(
            status_code=502,
            detail="Mitigation application failed",
        )

    application = {
        "selected_control": selected_control.value,
        "status": application_result["status"],
        "execution_info": application_result,
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }

    mitigation_repository.update_mitigation_run(
        payload.mitigation_run_id,
        status="applied",
        application=application,
    )

    return {
        "selected_control": selected_control.value,
        "status": application_result["status"],
        "execution_info": application_result,
    }


@app.post(
    "/experiments/{experiment_id}/mitigation/replay",
    response_model=BeforeAfterReplayResult,
)
def replay_mitigation_run(
    experiment_id: str,
    payload: MitigationReplayRequest,
):
    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    mitigation_run = mitigation_repository.get_mitigation_run(
        payload.mitigation_run_id
    )

    if (
        mitigation_run is None
        or mitigation_run.get("experiment_id") != experiment_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Mitigation run not found",
        )

    selection = mitigation_run.get("selection")
    selected_control_value = (
        selection.get("selected_control")
        if isinstance(selection, dict)
        else None
    )

    if not selected_control_value:
        raise HTTPException(
            status_code=409,
            detail="Mitigation run has no selected control",
        )

    try:
        selected_control = DefensiveControl(selected_control_value)
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=409,
            detail="Mitigation run has an invalid selected control",
        ) from error

    application = mitigation_run.get("application")
    if (
        mitigation_run.get("status") != "applied"
        or not isinstance(application, dict)
        or application.get("status") != "applied"
    ):
        raise HTTPException(
            status_code=409,
            detail="Mitigation control has not been applied",
        )

    expected_tests = {
        DefensiveControl.authorization_gate: "permission_test",
        DefensiveControl.tool_allowlist: "tool_access_test",
        DefensiveControl.memory_validation: "memory_access_test",
    }
    if expected_tests[selected_control] != payload.test:
        raise HTTPException(
            status_code=409,
            detail="Replay test does not match selected control",
        )

    try:
        p4_result = replay_attack(
            experiment_id,
            payload.test,
            selected_control.value,
        )
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Mitigation replay failed",
        ) from error

    required_fields = {
        "experiment_id",
        "test",
        "control",
        "before",
        "after",
        "activation",
        "before_validation",
        "after_validation",
        "disrupted",
        "residual_vulnerable_steps",
        "validation_result",
    }
    if (
        not isinstance(p4_result, dict)
        or p4_result.get("status") != "completed"
        or not required_fields.issubset(p4_result)
    ):
        raise HTTPException(
            status_code=502,
            detail="Mitigation replay returned an invalid result",
        )

    try:
        replay_result = BeforeAfterReplayResult(
            test=payload.test,
            before_result=p4_result["before"],
            after_result=p4_result["after"],
            blocked_after_mitigation=p4_result.get(
                "blocked_after_mitigation",
                p4_result.get("attack_disrupted"),
            ),
        )
        disruption_result = ChainDisruptionResult(
            chain_id=mitigation_run["chain_id"],
            before_validation=p4_result["before_validation"],
            after_validation=p4_result["after_validation"],
            disrupted=p4_result["disrupted"],
            residual_vulnerable_steps=p4_result[
                "residual_vulnerable_steps"
            ],
            validation_result=p4_result["validation_result"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="Mitigation replay returned an invalid result",
        ) from error

    replayed_at = datetime.now(timezone.utc).isoformat()
    research_record = build_mitigation_experiment_record(
        {
            "status": p4_result["status"],
            "experiment_id": p4_result["experiment_id"],
            "test": p4_result["test"],
            "control": p4_result["control"],
            "before": p4_result["before"],
            "after": p4_result["after"],
            "activation": p4_result["activation"],
            "before_validation": p4_result["before_validation"],
            "after_validation": p4_result["after_validation"],
            "disrupted": p4_result["disrupted"],
            "residual_vulnerable_steps": p4_result[
                "residual_vulnerable_steps"
            ],
            "validation_result": p4_result["validation_result"],
        },
        mode=experiment["mode"],
        mitigation_selected=None,
        llm_calls=selection.get("llm_calls", 0),
        fallback_used=selection.get("fallback_used", False),
    )

    mitigation_repository.update_mitigation_run(
        payload.mitigation_run_id,
        status="completed",
        replay={
            **replay_result.model_dump(),
            "replayed_at": replayed_at,
        },
        disruption=disruption_result.model_dump(),
    )
    db.evaluation_results.insert_one(
        {
            "evaluation_type": "phase2_mitigation",
            "timestamp": replayed_at,
            **research_record,
        }
    )

    return replay_result


@app.get(
    "/experiments/{experiment_id}/mitigation/result",
    response_model=MitigationResultResponse,
)
def get_mitigation_result(
    experiment_id: str,
    mitigation_run_id: str,
):
    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    mitigation_run = mitigation_repository.get_mitigation_run(
        mitigation_run_id
    )

    if (
        mitigation_run is None
        or mitigation_run.get("experiment_id") != experiment_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Mitigation run not found",
        )

    if mitigation_run.get("status") != "completed":
        raise HTTPException(
            status_code=409,
            detail="Mitigation run is not completed",
        )

    selection = mitigation_run["selection"]
    return MitigationResultResponse(
        mitigation_run_id=mitigation_run["mitigation_run_id"],
        experiment_id=mitigation_run["experiment_id"],
        chain_id=mitigation_run["chain_id"],
        status=mitigation_run["status"],
        selection={
            "mitigation_run_id": mitigation_run["mitigation_run_id"],
            "selected_control": selection["selected_control"],
            "reason": selection["reason"],
            "confidence": selection["confidence"],
        },
        application=mitigation_run["application"],
        replay=mitigation_run["replay"],
        disruption=mitigation_run["disruption"],
    )


@app.post("/experiments/{experiment_id}/start")
def start_experiment(
    experiment_id: str
):

    # ----------------------------------------
    # Check whether experiment exists
    # ----------------------------------------

    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    # ----------------------------------------
    # Set experiment to running
    # ----------------------------------------

    db.experiments.update_one(
        {"experiment_id": experiment_id},
        {"$set": {"status": "running"}},
    )

    add_experiment_log(
        experiment_id,
        "Experiment started",
    )

    # ----------------------------------------
    # Day 7 Adaptive Orchestration
    # ----------------------------------------

    available_tests = [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]

    previous_tests = []
    planner_findings = []
    executed_tests = []
    sandbox_results = []

    max_tests = experiment["max_tests"]

    # ----------------------------------------
    # Adaptive testing loop
    # ----------------------------------------

    for test_number in range(max_tests):

        # ----------------------------------------
        # P2 -> P3 Adaptive Planner
        # ----------------------------------------

        planner_input = PlannerInput(
            findings=planner_findings,
            previous_tests=previous_tests,
            available_tests=available_tests,
            retrieved_knowledge=[],
            chain_state={
                "experiment_id": experiment_id,
                "executed_tests": executed_tests,
            },
        )

        decision = planner.plan(
            planner_input
        )

        selected_test = decision.selected_test

        # ----------------------------------------
        # Prevent duplicate test execution
        # ----------------------------------------

        if selected_test in previous_tests:

            remaining_tests = [
                test
                for test in available_tests
                if test not in previous_tests
            ]

            if not remaining_tests:
                break

            selected_test = remaining_tests[0]

        add_experiment_log(
            experiment_id,
            f"Planner selected test: {selected_test}",
        )

        # ----------------------------------------
        # P2 -> P4 Sandbox
        # ----------------------------------------

        sandbox_result = execute_sandbox_test(
            experiment_id,
            selected_test,
        )

        sandbox_results.append(
            sandbox_result
        )

        add_experiment_log(
            experiment_id,
            f"Sandbox completed: {sandbox_result['test']}",
        )

        # ----------------------------------------
        # Store finding in MongoDB
        # ----------------------------------------

        add_experiment_finding(
            experiment_id=experiment_id,
            test=sandbox_result["test"],
            finding=sandbox_result["finding"],
            severity=sandbox_result["severity"],
            evidence=sandbox_result["evidence"],
            confidence=sandbox_result["confidence"],
        )

        # ----------------------------------------
        # Convert P4 result -> P3 Finding
        # ----------------------------------------

        planner_finding = Finding(
            finding=sandbox_result["finding"],
            severity=sandbox_result["severity"],
            confidence=sandbox_result["confidence"],
            evidence=str(
                sandbox_result["evidence"]
            ),
        )

        planner_findings.append(
            planner_finding
        )

        # ----------------------------------------
        # Update test history
        # ----------------------------------------

        previous_tests.append(
            selected_test
        )

        executed_tests.append(
            selected_test
        )

        # Remove executed test
        if selected_test in available_tests:

            available_tests.remove(
                selected_test
            )

        # ----------------------------------------
        # Stop when no tests remain
        # ----------------------------------------

        if not available_tests:
            break

    # ----------------------------------------
    # Candidate Chain
    # ----------------------------------------

    chain_id = None
    validation_result = None

    if executed_tests:

        chain_id = add_attack_chain(
            experiment_id=experiment_id,
            name="Adaptive Candidate Chain",
            steps=executed_tests,
        )

        add_experiment_log(
            experiment_id,
            f"Candidate chain created: {chain_id}",
        )

        # ----------------------------------------
        # P4 Chain Validation
        # ----------------------------------------

        validator = ChainValidator(
            experiment_id
        )

        validation_result = validator.validate_chain(
            chain_id,
            executed_tests,
        )

        # ----------------------------------------
        # Store validation result
        # ----------------------------------------

        db.evaluation_results.insert_one(
            {
                "experiment_id": experiment_id,
                "chain_id": chain_id,
                "status": validation_result["status"],
                "validated_steps": validation_result[
                    "validated_steps"
                ],
                "total_steps": validation_result[
                    "total_steps"
                ],
                "steps": validation_result["steps"],
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
            }
        )

        add_experiment_log(
            experiment_id,
            f"Chain validation completed: "
            f"{validation_result['status']}",
        )

    # ----------------------------------------
    # Complete experiment
    # ----------------------------------------

    db.experiments.update_one(
        {"experiment_id": experiment_id},
        {"$set": {"status": "completed"}},
    )

    add_experiment_log(
        experiment_id,
        "Experiment completed",
    )

    # ----------------------------------------
    # Return Day 7 result
    # ----------------------------------------

    return {
        "experiment_id": experiment_id,
        "status": "completed",
        "executed_tests": executed_tests,
        "findings_created": len(
            sandbox_results
        ),
        "sandbox_results": sandbox_results,
        "candidate_chain": {
            "chain_id": chain_id,
            "steps": executed_tests,
        },
        "validation_result": validation_result,
    }


@app.get("/experiments/{experiment_id}/status")
def get_experiment_status(
    experiment_id: str
):

    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    return {
        "experiment_id": experiment_id,
        "status": experiment["status"],
    }


@app.post("/chains/{chain_id}/validate")
def validate_chain(
    chain_id: str
):

    # ----------------------------------------
    # Find chain using our string chain_id
    # ----------------------------------------

    chain = db.attack_chains.find_one(
        {"chain_id": chain_id}
    )

    if chain is None:
        raise HTTPException(
            status_code=404,
            detail="Chain not found",
        )

    experiment_id = chain["experiment_id"]

    steps = chain.get(
        "steps",
        [],
    )

    # ----------------------------------------
    # Use P4 validator
    # ----------------------------------------

    validator = ChainValidator(
        experiment_id
    )

    validation_result = validator.validate_chain(
        chain_id,
        steps,
    )

    step_results = validation_result["steps"]
    execution_cost = {
        "test_count": sum(
            step.get("execution_cost", {}).get("test_count", 0)
            for step in step_results
            if isinstance(step.get("execution_cost"), dict)
        ),
        "execution_time_seconds": sum(
            step.get("execution_cost", {}).get(
                "execution_time_seconds",
                0.0,
            )
            for step in step_results
            if isinstance(step.get("execution_cost"), dict)
        ),
    }
    validation_result = {
        **validation_result,
        "execution_cost": execution_cost,
    }

    # ----------------------------------------
    # Store validation result
    # ----------------------------------------

    db.evaluation_results.insert_one(
        {
            "evaluation_type": "phase3_chain_validation",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "status": validation_result["status"],
            "validated_steps": validation_result[
                "validated_steps"
            ],
            "total_steps": validation_result[
                "total_steps"
            ],
            "chain_length": validation_result.get(
                "chain_length",
                validation_result["total_steps"],
            ),
            "validation_rate": validation_result.get(
                "validation_rate",
                0.0,
            ),
            "all_findings_reproduced": validation_result.get(
                "all_findings_reproduced",
                False,
            ),
            "steps": validation_result["steps"],
            "execution_cost": execution_cost,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }
    )

    return validation_result


@app.get("/analytics")
def get_analytics():
    mitigation_records = list(
        db.evaluation_results.find(
            {"evaluation_type": "phase2_mitigation"},
            {"_id": 0},
        )
    )

    return {
        "total_experiments": db.experiments.count_documents({}),
        "total_findings": db.findings.count_documents({}),
        "total_chains": db.attack_chains.count_documents({}),
        "total_evaluation_results": db.evaluation_results.count_documents({}),
        "mitigation_metrics": calculate_research_metrics(
            {"experiments": mitigation_records}
        ),
    }


@app.get("/phase2/analytics")
def get_phase2_analytics():
    records = list(
        db.evaluation_results.find(
            {
                "evaluation_type": "phase2_condition",
                "source": "phase2_condition_runner",
            },
            {"_id": 0},
        )
    )

    return {
        "metrics": calculate_phase2_metrics(records),
        "records": records,
    }


@app.post("/phase2/evaluation/run")
def run_phase2_evaluation():
    try:
        records = run_all_phase2_experiments()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Phase 2 evaluation run failed",
        ) from error

    try:
        persisted_count = persist_phase2_condition_records(records)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Phase 2 evaluation persistence failed",
        ) from error

    return {
        "status": "completed",
        "records_generated": len(records),
        "records_persisted": persisted_count,
    }
