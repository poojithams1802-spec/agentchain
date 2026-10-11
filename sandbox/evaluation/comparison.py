
def compare_evaluations(static_result, adaptive_result):
    """
    Compare static and adaptive evaluation results.

    Reports outcome metrics and measured execution costs.
    Positive differences mean the adaptive value is higher.
    A higher value is not automatically better.
    """

    static_cost = static_result.get("execution_cost") or {}
    adaptive_cost = adaptive_result.get("execution_cost") or {}

    static_test_count = static_cost.get("test_count")
    adaptive_test_count = adaptive_cost.get("test_count")

    static_execution_time = static_cost.get("execution_time_seconds")
    adaptive_execution_time = adaptive_cost.get("execution_time_seconds")

    comparison = {
        "total_tests_difference": (
            adaptive_result["total_tests"]
            - static_result["total_tests"]
        ),
        "total_findings_difference": (
            adaptive_result["total_findings"]
            - static_result["total_findings"]
        ),
        "candidate_chains_difference": (
            adaptive_result["candidate_chains"]
            - static_result["candidate_chains"]
        ),
        "validated_chains_difference": (
            adaptive_result["validated_chains"]
            - static_result["validated_chains"]
        ),
        "average_chain_length_difference": (
            adaptive_result["average_chain_length"]
            - static_result["average_chain_length"]
        ),
        "validation_rate_difference": (
            adaptive_result["validation_rate"]
            - static_result["validation_rate"]
        ),
        "static_execution_test_count": static_test_count,
        "adaptive_execution_test_count": adaptive_test_count,
        "execution_test_count_difference": (
            adaptive_test_count - static_test_count
            if static_test_count is not None
            and adaptive_test_count is not None
            else None
        ),
        "static_execution_time_seconds": static_execution_time,
        "adaptive_execution_time_seconds": adaptive_execution_time,
        "execution_time_difference_seconds": (
            adaptive_execution_time - static_execution_time
            if static_execution_time is not None
            and adaptive_execution_time is not None
            else None
        ),
        "static_execution_results_available": (
            static_test_count is not None
            and static_execution_time is not None
        ),
        "adaptive_execution_results_available": (
            adaptive_test_count is not None
            and adaptive_execution_time is not None
        ),
    }

    return {
        "static": static_result,
        "adaptive": adaptive_result,
        "comparison": comparison,
    }
