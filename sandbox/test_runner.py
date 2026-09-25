from vulnerabilities.v1_weak_permission import run_v1_scenario
from vulnerabilities.v2_unsafe_tool_access import run_v2_scenario
from vulnerabilities.v3_memory_validation import run_v3_scenario


TEST_MAP = {
    "permission_test": run_v1_scenario,
    "tool_access_test": run_v2_scenario,
    "memory_access_test": run_v3_scenario,
}


def run_test(test_name):
    if test_name not in TEST_MAP:
        return {
            "status": "failed",
            "test": test_name,
            "finding": None,
            "severity": None,
            "evidence": f"Unknown test: {test_name}"
        }

    result = TEST_MAP[test_name]()

    finding = result["name"]

    return {
        "status": "completed",
        "test": test_name,
        "finding": finding,
        "severity": result["severity"],
        "evidence": result["evidence"]
    }