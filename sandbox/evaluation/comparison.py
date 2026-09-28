def compare_evaluations(static_result, adaptive_result):
    """
    Compare static and adaptive evaluation results.

    This function reports metric differences without declaring
    either strategy as better.
    """

    return {
        "static": static_result,
        "adaptive": adaptive_result,
        "comparison": {
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
            )
        }
    }