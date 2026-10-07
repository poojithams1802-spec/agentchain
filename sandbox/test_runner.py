from .vulnerabilities.v1_weak_permission import run_v1_scenario
from .vulnerabilities.v2_unsafe_tool_access import run_v2_scenario
from .vulnerabilities.v3_memory_validation import run_v3_scenario
from .vulnerabilities.v4_prompt_injection import run_v4_scenario
from .vulnerabilities.v5_indirect_prompt_injection import (
    run_v5_scenario,
)
from .vulnerabilities.v6_sensitive_data_exposure import (
    run_v6_scenario,
)
from .vulnerabilities.v7_unsafe_file_operation import (
    run_v7_scenario,
)
from .vulnerabilities.v8_context_manipulation import (
    run_v8_scenario,
)
from .vulnerabilities.v9_privilege_propagation import (
    run_v9_scenario,
)
from sandbox.vulnerabilities.v10_unsafe_delegation import (
    run_v10_scenario,
)
from sandbox.vulnerabilities.v11_cross_agent_trust import (
    run_v11_scenario,
)
from .vulnerabilities.v12_tool_parameter_validation import (
    run_v12_scenario,
)

def test_v11_cross_agent_trust():
    result = run_v11_scenario()

    assert result["vulnerability_id"] == "V11"
    assert result["name"] == "cross_agent_trust_weakness"
    assert result["test"] == "cross_agent_trust_test"

    assert result["expected"] == "untrusted_agent_rejected"
    assert result["actual"] == "untrusted_agent_trusted"

    assert result["vulnerable"] is True
    assert result["severity"] == "high"

    assert result["evidence"]
    assert result["validation_rule"]


def test_v10_unsafe_delegation():
    result = run_v10_scenario()

    assert result["vulnerability_id"] == "V10"
    assert result["name"] == "unsafe_delegation"
    assert result["test"] == "unsafe_delegation_test"

    assert result["expected"] == "delegation_denied"
    assert result["actual"] == "delegation_allowed"

    assert result["vulnerable"] is True
    assert result["severity"] == "high"

    assert result["evidence"]
    assert result["validation_rule"]
TEST_MAP = {
    "permission_test": run_v1_scenario,
    "tool_access_test": run_v2_scenario,
    "memory_access_test": run_v3_scenario,
    "prompt_injection_test": run_v4_scenario,
    "indirect_prompt_injection_test": run_v5_scenario,
    "sensitive_data_test": run_v6_scenario,
    "file_operation_test": run_v7_scenario,
    "context_manipulation_test": run_v8_scenario,
    "privilege_propagation_test": run_v9_scenario,
    "unsafe_delegation_test": run_v10_scenario,
    "cross_agent_trust_test": run_v11_scenario,
    "tool_parameter_validation_test": run_v12_scenario,
}


def run_test(test_name):
    if test_name not in TEST_MAP:
        return {
            "status": "failed",
            "test": test_name,
            "finding": None,
            "severity": None,
            "evidence": f"Unknown test: {test_name}",
            "confidence": 0.0
        }

    result = TEST_MAP[test_name]()

    finding = result["name"]

    # The current P4 scenarios are deterministic.
    # If the intentionally vulnerable behavior is reproduced,
    # confidence is 1.0.
    # Otherwise confidence is 0.0.
    confidence = 1.0 if result["vulnerable"] else 0.0

    return {
        "status": "completed",
        "test": test_name,
        "finding": finding,
        "severity": result["severity"],
        "evidence": result["evidence"],
        "confidence": confidence
    }