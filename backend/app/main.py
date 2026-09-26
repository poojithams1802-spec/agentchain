from datetime import datetime, timezone
import os
import sys
import uuid

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from app.database import db
from app.schemas import ExperimentCreate

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
from sandbox.execution.sandbox_executor import execute_sandbox_test
from sandbox.validator.chain_validator import ChainValidator


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

    return validation_result


@app.get("/analytics")
def get_analytics():

    return {
        "total_experiments": db.experiments.count_documents({}),
        "total_findings": db.findings.count_documents({}),
        "total_chains": db.attack_chains.count_documents({}),
        "total_evaluation_results": db.evaluation_results.count_documents({}),
    }