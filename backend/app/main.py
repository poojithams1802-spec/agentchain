from datetime import datetime, timezone
import os
import sys

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from app.database import db
from app.schemas import ExperimentCreate

# Load environment variables
load_dotenv("backend/.env")

# Make ai-engine available
sys.path.append(os.path.abspath("../../ai-engine"))

from planner import AdaptivePlanner
from schemas import PlannerInput


app = FastAPI()

# Initialize P3 planner
planner = AdaptivePlanner()


def add_experiment_log(experiment_id: str, message: str) -> None:
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
    evidence: str,
) -> None:
    finding_entry = {
        "experiment_id": experiment_id,
        "test": test,
        "finding": finding,
        "severity": severity,
        "evidence": evidence,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    db.findings.insert_one(finding_entry)


def add_attack_chain(
    experiment_id: str,
    name: str,
    steps: list[str],
) -> None:
    chain_entry = {
        "experiment_id": experiment_id,
        "name": name,
        "steps": steps,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    db.attack_chains.insert_one(chain_entry)


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
    experiments = list(db.experiments.find({}))

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
def get_experiment(experiment_id: str):
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
def get_experiment_logs(experiment_id: str):
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
def get_experiment_findings(experiment_id: str):
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
def get_experiment_chains(experiment_id: str):
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
def start_experiment(experiment_id: str):

    # Check whether experiment exists
    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    # Set experiment to running
    db.experiments.update_one(
        {"experiment_id": experiment_id},
        {"$set": {"status": "running"}},
    )

    add_experiment_log(
        experiment_id,
        "Experiment started",
    )

    # ----------------------------------------
    # P2 -> P3 Adaptive Planner
    # ----------------------------------------

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[],
        chain_state={},
    )

    # Ask P3 planner to select the next test
    decision = planner.plan(planner_input)

    selected_test = decision.selected_test

    # ----------------------------------------
    # Temporary mock sandbox result
    # ----------------------------------------

    add_experiment_finding(
        experiment_id=experiment_id,
        test=selected_test,
        finding="Mock finding from sandbox",
        severity="medium",
        evidence="Mock evidence for orchestration testing",
    )

    add_experiment_log(
        experiment_id,
        f"Planner selected test: {selected_test}",
    )

    # Set experiment to completed
    db.experiments.update_one(
        {"experiment_id": experiment_id},
        {"$set": {"status": "completed"}},
    )

    add_experiment_log(
        experiment_id,
        "Experiment completed",
    )

    return {
        "experiment_id": experiment_id,
        "status": "completed",
        "executed_tests": [selected_test],
        "findings_created": 1,
        "planner_decision": {
            "selected_test": decision.selected_test,
            "reason": decision.reason,
            "priority": decision.priority,
            "confidence": decision.confidence,
        },
    }


@app.get("/experiments/{experiment_id}/status")
def get_experiment_status(experiment_id: str):

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
def validate_chain(chain_id: str):

    chain = db.attack_chains.find_one(
        {"_id": chain_id}
    )

    if chain is None:
        raise HTTPException(
            status_code=404,
            detail="Chain not found",
        )

    validated_steps = chain.get(
        "steps",
        [],
    )

    return {
        "chain_id": chain_id,
        "status": "validated",
        "validated_steps": validated_steps,
    }


@app.get("/analytics")
def get_analytics():

    return {
        "total_experiments": db.experiments.count_documents({}),
        "total_findings": db.findings.count_documents({}),
        "total_chains": db.attack_chains.count_documents({}),
    }