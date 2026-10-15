from datetime import datetime, timezone
import logging
import os
import sys
import uuid
import inspect

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

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

from app.database import db
from app.schemas import (
    BeforeAfterReplayResult,
    ChainExecutionRequest,
    ChainExecutionResponse,
    ChainMitigationReplayRequest,
    ChainP4AssociationRequest,
    ChainDisruptionResult,
    ControlApplicationResult,
    DefensiveControl,
    ExperimentCreate,
    MitigationApplyRequest,
    MitigationReplayRequest,
    MitigationResultResponse,
    MitigationSelectionRequest,
    AblationResultCreate,
    AgentStateCreate,
    MultiAgentSecurityResultCreate,
)
import app.mitigation_repository as mitigation_repository
from app.scenario_config import get_all_scenarios, get_scenario
from app.ablation_persistence import (
    persist_ablation_result,
)
from app.ablation_aggregation import (
    get_persisted_ablation_aggregation,
)

from planner import AdaptivePlanner
from schemas import PlannerInput, Finding
from adaptive_loop import AdaptiveLoop
from mitigation_schemas import (
    MitigationFinding,
    MitigationSelectorInput,
)
from mitigation_selector import MitigationSelector
from sandbox.mitigation.mitigation_executor import (
    CONTROL_TARGETS,
    apply_mitigation,
)
from sandbox.mitigation.replay_executor import replay_attack
from sandbox.chains.chain_executor import (
    execute_chain,
    chain_result_to_research_result,
)
from sandbox.chains.chain_replay_executor import replay_chain
from sandbox.chains.chain_registry import (
    get_chain as get_registered_chain,
)
from sandbox.evaluation.mitigation_evaluation import (
    build_mitigation_experiment_record,
)
from sandbox.evaluation.phase2_runner import run_all_phase2_experiments
from sandbox.evaluation.phase2_metrics import calculate_phase2_metrics
from sandbox.evaluation.research_metrics import calculate_research_metrics
from sandbox.execution.adaptive_test_executor import execute_selected_test
from sandbox.execution.sandbox_executor import ALLOWED_TESTS
from sandbox.test_runner import VULNERABILITY_TEST_MAP
from sandbox.validator.chain_validator import (
    EXPECTED_FINDINGS,
    ChainValidator,
)
from sandbox.agent.multi_agent_security import (
    run_and_validate_multi_agent_security_scenario,
)
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


def _resolve_experiment_tests(experiment: dict) -> list[str]:
    """Resolve the approved sandbox tests for the experiment.

    Preserve the original legacy default when no Phase 3 scenario fields were
    provided. If the caller explicitly selects a registered scenario or
    vulnerability set, use only tests from that registered chain metadata and
    reject unknown scenario IDs or incompatible vulnerability IDs.
    """
    legacy_default_tests = [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]

    scenario_id = experiment.get("scenario_id")
    vulnerability_ids = experiment.get("vulnerability_ids") or []

    if not scenario_id and not vulnerability_ids:
        return legacy_default_tests

    if scenario_id:
        scenario = get_scenario(scenario_id)
        if scenario is None:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario not found: {scenario_id}",
            )
        ordered_tests = []
        seen = set()
        for step in scenario.get("steps", []):
            if step in ALLOWED_TESTS and step not in seen:
                ordered_tests.append(step)
                seen.add(step)
        if not ordered_tests:
            raise HTTPException(
                status_code=400,
                detail=f"Scenario {scenario_id} does not expose approved sandbox tests.",
            )
        return ordered_tests

    requested_vulnerabilities = [
        vulnerability_id
        for vulnerability_id in vulnerability_ids
        if isinstance(vulnerability_id, str) and vulnerability_id.strip()
    ]
    if not requested_vulnerabilities:
        return legacy_default_tests

    def canonical_vulnerability_id(vulnerability_id: str) -> str:
        value = vulnerability_id.strip().upper()
        if value.startswith("V") and value[1:].isdigit():
            return f"V{int(value[1:])}"
        return value

    vulnerability_test_map = {
        canonical_vulnerability_id(vulnerability_id): test_name
        for vulnerability_id, test_name in VULNERABILITY_TEST_MAP.items()
    }
    unsupported = [
        vulnerability_id
        for vulnerability_id in requested_vulnerabilities
        if canonical_vulnerability_id(vulnerability_id)
        not in vulnerability_test_map
    ]
    if unsupported:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported vulnerability IDs for approved Phase 3 testing: "
                + ", ".join(sorted(unsupported))
            ),
        )

    ordered_tests = [
        vulnerability_test_map[canonical_vulnerability_id(vulnerability_id)]
        for vulnerability_id in requested_vulnerabilities
    ]

    if not ordered_tests:
        raise HTTPException(
            status_code=400,
            detail=(
                "Requested vulnerability IDs do not resolve to any registered "
                "approved sandbox tests."
            ),
        )
    return ordered_tests


def _p4_chain_definition_mismatch(
    chain: dict,
    definition: dict,
    require_stored_dependencies: bool,
) -> str | None:
    definition_steps = definition.get("steps")
    if (
        not isinstance(definition_steps, list)
        or chain.get("steps") != definition_steps
    ):
        return "ordered steps do not match"

    if (
        "ordered_steps" in definition
        and definition.get("ordered_steps") != definition_steps
    ):
        return "registered ordered steps are inconsistent"

    definition_dependencies = definition.get("dependencies")
    if not isinstance(definition_dependencies, dict):
        return "registered dependencies are invalid"

    stored_dependencies = chain.get("dependencies")
    if "dependencies" not in chain:
        if require_stored_dependencies:
            return "stored dependencies are missing"
    elif stored_dependencies != definition_dependencies:
        return "dependencies do not match"

    stored_ordered_steps = chain.get("ordered_steps")
    if (
        "ordered_steps" in chain
        and stored_ordered_steps != definition_steps
    ):
        return "stored ordered steps do not match"

    return None


def _replay_step_validations(steps: list[str], results: object):
    if not isinstance(results, list) or len(results) != len(steps):
        return None

    validations = []
    for step, result in zip(steps, results):
        if (
            not isinstance(result, dict)
            or result.get("test") != step
            or not isinstance(result.get("status"), str)
            or (
                result.get("finding") is not None
                and not isinstance(result.get("finding"), str)
            )
            or "evidence" not in result
        ):
            return None

        expected_finding = EXPECTED_FINDINGS.get(step)
        finding_matches = result.get("finding") == expected_finding
        evidence_exists = bool(result.get("evidence"))
        valid = (
            result.get("status") == "completed"
            and finding_matches
            and evidence_exists
        )
        validations.append(
            {
                "valid": valid,
                "test": step,
                "status": result.get("status"),
                "finding": result.get("finding"),
                "expected_finding": expected_finding,
                "finding_matches": finding_matches,
                "evidence_exists": evidence_exists,
                "error": (
                    None
                    if valid
                    else "Chain step validation failed."
                ),
            }
        )

    return validations


def _replay_validation_matches(
    validation: object,
    step_validations: list[dict],
    steps: list[str],
) -> bool:
    if not isinstance(validation, dict):
        return False

    valid_count = sum(
        item["valid"]
        for item in step_validations
    )
    total_steps = len(steps)
    expected_values = {
        "valid": total_steps > 0 and valid_count == total_steps,
        "validated_steps": valid_count,
        "total_steps": total_steps,
        "validation_rate": valid_count / total_steps if total_steps else 0.0,
        "steps": step_validations,
    }
    for key, expected in expected_values.items():
        actual = validation.get(key)
        if key == "validated_steps" or key == "total_steps":
            if type(actual) is not int or actual != expected:
                return False
        elif key == "validation_rate":
            if (
                isinstance(actual, bool)
                or not isinstance(actual, (int, float))
                or actual != expected
            ):
                return False
        elif key == "valid":
            if type(actual) is not bool or actual is not expected:
                return False
        elif actual != expected:
            return False

    actual_steps = validation.get("steps")
    if not isinstance(actual_steps, list) or len(actual_steps) != len(
        step_validations
    ):
        return False
    for actual, expected in zip(actual_steps, step_validations):
        if not isinstance(actual, dict):
            return False
        if (
            type(actual.get("valid")) is not bool
            or type(actual.get("finding_matches")) is not bool
            or type(actual.get("evidence_exists")) is not bool
            or any(
                actual.get(key) != value
                for key, value in expected.items()
            )
        ):
            return False

    return True


def _valid_chain_replay_result(
    result: object,
    experiment_id: str,
    p4_chain_id: str,
    control_name: str,
    definition: dict,
) -> bool:
    if not isinstance(result, dict):
        return False

    steps = definition.get("steps")
    if (
        not isinstance(steps, list)
        or not steps
        or result.get("status") != "completed"
        or not isinstance(result.get("chain_id"), str)
        or not result["chain_id"]
        or result["chain_id"] != p4_chain_id
        or result.get("experiment_id") != experiment_id
        or result.get("control") != control_name
        or result.get("chain_name") != definition.get("name")
        or result.get("chain_description") != definition.get("description")
        or result.get("chain_steps") != steps
        or type(result.get("chain_length")) is not int
        or result["chain_length"] != len(steps)
    ):
        return False

    before_validations = _replay_step_validations(
        steps,
        result.get("before"),
    )
    after_validations = _replay_step_validations(
        steps,
        result.get("after"),
    )
    if (
        before_validations is None
        or after_validations is None
        or not _replay_validation_matches(
            result.get("before_validation"),
            before_validations,
            steps,
        )
        or not _replay_validation_matches(
            result.get("after_validation"),
            after_validations,
            steps,
        )
    ):
        return False

    control_details = CONTROL_TARGETS.get(control_name)
    activation = result.get("activation")
    if (
        control_details is None
        or not isinstance(activation, dict)
        or activation.get("status") != "applied"
        or activation.get("experiment_id") != experiment_id
        or activation.get("control") != control_name
        or activation.get("target") != control_details["target"]
        or activation.get("test") != control_details["test"]
        or not isinstance(activation.get("evidence"), str)
        or not activation["evidence"]
    ):
        return False

    activation_result = activation.get("activation")
    if (
        not isinstance(activation_result, dict)
        or activation_result.get("status") != "activated"
        or activation_result.get("experiment_id") != experiment_id
        or activation_result.get("control") != control_name
        or not isinstance(activation_result.get("evidence"), str)
        or not activation_result["evidence"]
    ):
        return False

    blocked_steps = []
    for step, step_result in zip(steps, result["after"]):
        evidence = step_result.get("evidence")
        blocked_marker = (
            isinstance(evidence, dict)
            and evidence.get("result") == "attack_blocked"
        )
        mitigation_applied = step_result.get("mitigation_applied")
        if (
            ("mitigation_applied" in step_result and
             type(mitigation_applied) is not bool)
            or (blocked_marker and mitigation_applied is not True)
            or (mitigation_applied is True and not blocked_marker)
        ):
            return False
        if mitigation_applied is True and blocked_marker:
            if (
                step != control_details["test"]
                or step_result.get("mitigation_control") != control_name
                or evidence.get("mitigation") != control_name
                or evidence.get("mitigation_status") != "active"
            ):
                return False
            blocked_steps.append(step)

    residual_steps = [
        step for step in steps
        if step not in blocked_steps
    ]
    chain_disrupted = bool(blocked_steps)
    if (
        result.get("blocked_steps") != blocked_steps
        or result.get("residual_vulnerable_steps") != residual_steps
        or type(result.get("chain_disrupted")) is not bool
        or result["chain_disrupted"] != chain_disrupted
    ):
        return False

    before_valid = result["before_validation"]["valid"]
    after_valid = result["after_validation"]["valid"]
    validation_success = before_valid and after_valid and chain_disrupted
    validation_result = result.get("validation_result")
    if not isinstance(validation_result, dict):
        return False
    expected_validation_result = {
        "status": "validated" if validation_success else "invalid",
        "before_valid": before_valid,
        "after_valid": after_valid,
        "chain_disrupted": chain_disrupted,
        "blocked_steps": blocked_steps,
        "residual_vulnerable_steps": residual_steps,
        "attack_blocked": chain_disrupted,
        "validation_rate": 1.0 if validation_success else 0.0,
    }
    for key, expected in expected_validation_result.items():
        actual = validation_result.get(key)
        if key in {
            "before_valid",
            "after_valid",
            "chain_disrupted",
            "attack_blocked",
        }:
            if type(actual) is not bool or actual is not expected:
                return False
        elif key == "validation_rate":
            if (
                isinstance(actual, bool)
                or not isinstance(actual, (int, float))
                or actual != expected
            ):
                return False
        elif actual != expected:
            return False

    reset = result.get("reset")
    return (
        isinstance(reset, dict)
        and reset.get("status") == "reset"
        and reset.get("experiment_id") == experiment_id
        and isinstance(reset.get("evidence"), str)
        and bool(reset["evidence"])
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/scenarios")
def list_scenarios():
    """Return all controlled Phase 3 scenario configurations."""
    return {
        "scenarios": get_all_scenarios()
    }


@app.get("/scenarios/{scenario_id}")
def get_scenario_config(scenario_id: str):
    """Return one controlled Phase 3 scenario configuration."""
    scenario = get_scenario(scenario_id)

    if scenario is None:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario not found: {scenario_id}",
        )

    return scenario


@app.post("/experiments")
def create_experiment(payload: ExperimentCreate):

    experiment_count = db.experiments.count_documents({}) + 1

    experiment_id = f"EXP{experiment_count:03d}"

    experiment = {
        "experiment_id": experiment_id,
        "name": payload.name,
        "mode": payload.mode,
        "max_tests": payload.max_tests,
        "testing_budget": payload.testing_budget,
        "scenario_id": payload.scenario_id,
        "scenario_name": payload.scenario_name,
        "vulnerability_ids": payload.vulnerability_ids,
        "budget_used": 0,
        "selected_tests": [],
        "executed_tests": [],
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
            "testing_budget": item.get("testing_budget"),
            "scenario_id": item.get("scenario_id"),
            "scenario_name": item.get("scenario_name"),
            "vulnerability_ids": item.get("vulnerability_ids", []),
            "budget_used": item.get("budget_used", 0),
            "selected_tests": item.get("selected_tests", []),
            "executed_tests": item.get("executed_tests", []),
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
        "testing_budget": experiment.get("testing_budget"),
        "scenario_id": experiment.get("scenario_id"),
        "scenario_name": experiment.get("scenario_name"),
        "vulnerability_ids": experiment.get("vulnerability_ids", []),
        "budget_used": experiment.get("budget_used", 0),
        "selected_tests": experiment.get("selected_tests", []),
        "executed_tests": experiment.get("executed_tests", []),
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


@app.get("/experiments/{experiment_id}/adaptive-run")
def get_adaptive_run(experiment_id: str):
    experiment = db.experiments.find_one(
        {"experiment_id": experiment_id}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found",
        )

    adaptive_run = db.adaptive_run_results.find_one(
        {"experiment_id": experiment_id},
        {"_id": 0},
        sort=[("timestamp", -1)],
    )

    if adaptive_run is None:
        raise HTTPException(
            status_code=404,
            detail="No adaptive-run data found for this experiment",
        )

    return adaptive_run


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

    chain_definition = {
        "chain_id": chain["chain_id"],
        "name": chain.get(
            "name",
            chain.get("chain_name", "Adaptive Candidate Chain"),
        ),
        "description": chain.get(
            "description",
            "Experiment-generated adaptive candidate chain.",
        ),
        "steps": chain["steps"],
        "dependencies": chain.get("dependencies", {}),
    }

    execute_chain_parameters = inspect.signature(execute_chain).parameters

    if (
        "chain_definition" in execute_chain_parameters
        or any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in execute_chain_parameters.values()
        )
    ):
        result = execute_chain(
            experiment_id,
            payload.chain_id,
            chain_definition=chain_definition,
        )
    else:
        result = execute_chain(
            experiment_id,
            payload.chain_id,
        )

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


@app.post(
    "/experiments/{experiment_id}/chains/{chain_id}/p4-association",
)
def associate_experiment_chain_with_p4(
    experiment_id: str,
    chain_id: str,
    payload: ChainP4AssociationRequest,
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
            "chain_id": chain_id,
            "experiment_id": experiment_id,
        }
    )
    if chain is None:
        raise HTTPException(
            status_code=404,
            detail="Chain not found",
        )

    definition = get_registered_chain(payload.p4_chain_id)
    if definition is None:
        raise HTTPException(
            status_code=404,
            detail="Registered P4 chain not found",
        )

    mismatch = _p4_chain_definition_mismatch(
        chain,
        definition,
        require_stored_dependencies=False,
    )
    if mismatch is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Chain is incompatible with the selected P4 definition: {mismatch}",
        )

    update_result = db.attack_chains.update_one(
        {
            "chain_id": chain_id,
            "experiment_id": experiment_id,
        },
        {
            "$set": {
                "p4_chain_id": payload.p4_chain_id,
                "dependencies": definition["dependencies"],
            }
        },
    )
    already_associated = (
        chain.get("p4_chain_id") == payload.p4_chain_id
        and chain.get("dependencies") == definition["dependencies"]
    )
    if (
        update_result is None
        or getattr(update_result, "acknowledged", False) is not True
        or getattr(update_result, "matched_count", 0) != 1
        or (
            getattr(update_result, "modified_count", 0) != 1
            and not already_associated
        )
    ):
        raise HTTPException(
            status_code=409,
            detail="Chain association could not be persisted",
        )

    return {
        "chain_id": chain_id,
        "p4_chain_id": payload.p4_chain_id,
    }


@app.post(
    "/experiments/{experiment_id}/chains/mitigation/replay",
)
def replay_experiment_chain_mitigation(
    experiment_id: str,
    payload: ChainMitigationReplayRequest,
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

    p4_chain_id = chain.get("p4_chain_id")
    if not isinstance(p4_chain_id, str) or not p4_chain_id:
        raise HTTPException(
            status_code=409,
            detail="Chain has no registered P4 association",
        )

    definition = get_registered_chain(p4_chain_id)
    if definition is None:
        raise HTTPException(
            status_code=409,
            detail="Chain references an unknown registered P4 definition",
        )

    mismatch = _p4_chain_definition_mismatch(
        chain,
        definition,
        require_stored_dependencies=True,
    )
    if mismatch is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Chain is incompatible with its registered P4 definition: {mismatch}",
        )

    try:
        result = replay_chain(
            experiment_id,
            p4_chain_id,
            payload.control_name.value,
        )
    except Exception as error:
        logging.warning(
            "Full-chain mitigation replay raised exception: "
            "exception_type=%s",
            type(error).__name__,
        )
        raise HTTPException(
            status_code=502,
            detail="Full-chain mitigation replay failed",
        ) from None

    if not isinstance(result, dict) or result.get("status") != "completed":
        status_category = (
            "failed"
            if isinstance(result, dict) and result.get("status") == "failed"
            else "non_completed"
        )
        logging.warning(
            "Full-chain mitigation replay result invalid: "
            "result_type=%s status_category=%s missing_fields=%s",
            type(result).__name__,
            status_category,
            [],
        )
        raise HTTPException(
            status_code=502,
            detail="Full-chain mitigation replay returned an invalid result",
        )

    if not _valid_chain_replay_result(
        result,
        experiment_id,
        p4_chain_id,
        payload.control_name.value,
        definition,
    ):
        logging.warning(
            "Full-chain mitigation replay result failed contract validation"
        )
        raise HTTPException(
            status_code=502,
            detail="Full-chain mitigation replay returned an invalid result",
        )

    result = {
        **result,
        "chain_id": payload.chain_id,
        "p4_chain_id": p4_chain_id,
    }

    db.evaluation_results.insert_one(
        {
            **result,
            "evaluation_type": "phase3_chain_mitigation_replay",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

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
            "llm_called": selector_metrics.get("llm_called", False),
            "llm_success": selector_metrics.get("llm_success", False),
            "llm_error": selector_metrics.get("llm_error"),
            "retrieved_documents": selector_metrics.get(
                "retrieved_documents",
                0,
            ),
            "rag_time_seconds": selector_metrics.get(
                "rag_time_seconds",
                0.0,
            ),
            "prompt_build_time_seconds": selector_metrics.get(
                "prompt_build_time_seconds",
                0.0,
            ),
            "llm_time_seconds": selector_metrics.get(
                "llm_time_seconds",
                0.0,
            ),
            "total_time_seconds": selector_metrics.get(
                "total_time_seconds",
                0.0,
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
        not isinstance(application, dict)
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
    response_model_exclude_unset=True,
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
            **{
                field: selection[field]
                for field in (
                    "llm_called",
                    "llm_success",
                    "llm_error",
                    "retrieved_documents",
                    "rag_time_seconds",
                    "prompt_build_time_seconds",
                    "llm_time_seconds",
                    "total_time_seconds",
                )
                if field in selection
            },
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
    # Atomically claim experiment to prevent duplicate starts
    # ----------------------------------------

    start_result = db.experiments.update_one(
        {
            "experiment_id": experiment_id,
            "status": {"$nin": ["running", "completed"]},
        },
        {
            "$set": {
                "status": "running",
                "selected_tests": [],
                "executed_tests": [],
            }
        },
    )

    if start_result.modified_count != 1:
        raise HTTPException(
            status_code=409,
            detail="Experiment is already running or has completed and cannot be started again.",
        )

    # ----------------------------------------
    # Day 7 Adaptive Orchestration
    # ----------------------------------------

    available_tests = _resolve_experiment_tests(experiment)

    max_tests = min(
        int(experiment["max_tests"]),
        len(available_tests),
    )

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=available_tests,
        retrieved_knowledge=[],
        chain_state={
            "experiment_id": experiment_id,
            "executed_tests": [],
        },
    )

    adaptive_loop = AdaptiveLoop(planner=planner)

    # Run the adaptive loop exactly once. It already executes
    # each selected test through P3's adapter and P4's sandbox.
    try:
        detailed_result = adaptive_loop.run_detailed(
            planner_input=planner_input,
            experiment_id=experiment_id,
            max_tests=max_tests,
        )
    except Exception as exc:
        db.experiments.update_one(
            {
                "experiment_id": experiment_id,
                "status": "running",
            },
            {
                "$set": {
                    "status": "failed",
                    "error": str(exc),
                }
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Adaptive experiment execution failed.",
        ) from exc


    selected_tests = detailed_result["selected_tests"]
    sandbox_results = detailed_result["execution_results"]

    # Only successfully completed executions are used to construct
    # the candidate chain. Failed attempts remain in sandbox_results.
    executed_tests = [
        result["test"]
        for result in sandbox_results
        if result.get("status") == "completed"
    ]

    # Persist each raw execution result without rerunning it.
    for result in sandbox_results:
        test_name = result.get("test", "unknown_test")

        add_experiment_log(
            experiment_id,
            f"Adaptive execution result: {test_name} - "
            f"{result.get('status', 'unknown')}",
        )

        if result.get("status") == "failed":
            add_experiment_log(
                experiment_id,
                f"Sandbox execution failed: {test_name}",
            )
            continue

        add_experiment_finding(
            experiment_id=experiment_id,
            test=test_name,
            finding=result["finding"],
            severity=result["severity"],
            evidence=result["evidence"],
            confidence=result["confidence"],
        )

    # Store the detailed adaptive-run record, including raw execution
    # evidence, decisions, metadata, and budget counters.
    db.adaptive_run_results.insert_one(
        {
            "experiment_id": experiment_id,
            "status": detailed_result["status"],
            "tests_used": detailed_result["tests_used"],
            "selected_tests": selected_tests,
            "decisions": detailed_result["decisions"],
            "decision_metadata": detailed_result["decision_metadata"],
            "execution_results": sandbox_results,
            "findings": [
                finding.model_dump()
                for finding in detailed_result["findings"]
            ],
            "llm_calls": detailed_result["llm_calls"],
            "fallback_used": detailed_result["fallback_used"],
            "budget_used": detailed_result["budget_used"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    previous_budget_used = experiment.get("budget_used", 0)
    budget_used = detailed_result["budget_used"]
    tests_used_for_budget = budget_used["tests"]

    db.experiments.update_one(
        {"experiment_id": experiment_id},
        {
            "$set": {
                "selected_tests": selected_tests,
                "executed_tests": executed_tests,
                "budget_used": previous_budget_used + tests_used_for_budget,
                "adaptive_budget_used": budget_used,
            }
        },
    )


    add_experiment_log(
        experiment_id,
        f"Adaptive loop completed: {len(sandbox_results)} attempts, "
        f"{len(executed_tests)} successful executions",
    )

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
        {
            "$set": {
                "status": "completed",
                "selected_tests": selected_tests,
                "executed_tests": executed_tests,
            }
        },
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
        "findings_created": len(detailed_result["findings"]),
        "sandbox_results": sandbox_results,
        "candidate_chain": {
            "chain_id": chain_id,
            "steps": executed_tests,
        },
        "validation_result": validation_result,

        # Adaptive loop details for P3/P4 verification
        "tests_used": detailed_result["tests_used"],
        "selected_tests": selected_tests,
        "decisions": detailed_result["decisions"],
        "decision_metadata": detailed_result["decision_metadata"],
        "execution_results": sandbox_results,
        "llm_calls": detailed_result["llm_calls"],
        "fallback_used": detailed_result["fallback_used"],
        "budget_used": detailed_result["budget_used"],
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

@app.get("/phase3/analytics")
def get_phase3_analytics():
    records = list(
        db.evaluation_results.find(
            {
                "evaluation_type": "phase3_chain",
            },
            {"_id": 0},
        )
    )

    return {
        "metrics": calculate_research_metrics(
            {"experiments": records}
        ),
        "records": records,
    }

@app.post("/phase3/ablation/results")
def create_phase3_ablation_result(payload: AblationResultCreate):
    result = persist_ablation_result(
        payload.model_dump(),
        db.evaluation_results,
    )
    return {
        "ablation_run_id": result["ablation_run_id"],
        "experiment_id": result["experiment_id"],
        "configuration": result["configuration"],
        "status": result["status"],
    }


@app.get("/phase3/ablation/results")
def get_phase3_ablation_results():
    records = list(
        db.evaluation_results.find(
            {
                "evaluation_type": "phase3_ablation",
            },
            {"_id": 0},
        )
    )

    return {
        "results": records,
    }

@app.get("/phase3/ablation/aggregation")
def get_phase3_ablation_aggregation():
    return get_persisted_ablation_aggregation(db.evaluation_results)

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

@app.post("/experiments/{experiment_id}/agents/state")
def create_agent_state(
    experiment_id: str,
    payload: AgentStateCreate,
):
    document = {
        "experiment_id": experiment_id,
        "agents": payload.agents,
        "interactions": payload.interactions,
        "trust_context": payload.trust_context,
        "shared_memory_context": payload.shared_memory_context,
        "current_agent": payload.current_agent,
        "current_task": payload.current_task,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    db.agent_states.insert_one(document)

    return {
        "status": "success",
        "experiment_id": experiment_id,
    }

@app.post("/experiments/{experiment_id}/agents/security-result")
def create_multi_agent_security_result(
    experiment_id: str,
    payload: MultiAgentSecurityResultCreate,
):
    document = {
        "experiment_id": experiment_id,
        "agents": payload.agents,
        "interactions": payload.interactions,
        "trust_context": payload.trust_context,
        "shared_memory_context": payload.shared_memory_context,
        "assessment": payload.assessment,
        "status": payload.status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    db.multi_agent_results.insert_one(document)

    return {
        "status": "success",
        "experiment_id": experiment_id,
    }

@app.get("/experiments/{experiment_id}/agents/security-result")
def get_multi_agent_security_result(experiment_id: str):
    result = db.multi_agent_results.find_one(
        {"experiment_id": experiment_id},
        {"_id": 0},
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Multi-agent security result not found for "
                f"experiment: {experiment_id}"
            ),
        )

    return result


@app.post("/experiments/{experiment_id}/agents/security-result/run")
def run_multi_agent_security_result(experiment_id: str):
    # Execute and validate P4's controlled security scenario.
    result = run_and_validate_multi_agent_security_scenario()

    # Attach the experiment ID and persistence timestamp.
    document = {
        "experiment_id": experiment_id,
        **result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Save the actual scenario output in MongoDB.
    db.multi_agent_results.insert_one(document)

    return {
        "status": "success",
        "experiment_id": experiment_id,
        "chain_id": result["chain_id"],
        "chain_triggered": result["chain_triggered"],
        "validation": result["validation"],
    }

@app.get("/experiments/{experiment_id}/agents/state")
def get_agent_state(experiment_id: str):
    state = db.agent_states.find_one(
        {"experiment_id": experiment_id},
        {"_id": 0},
    )

    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent state not found for experiment: {experiment_id}",
        )

    return state
