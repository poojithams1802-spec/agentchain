def build_day7_result_record(experiment_result):
    """
    Normalize one completed Day-7 experiment into a
    reproducible research-dataset record.
    """

    if not isinstance(experiment_result, dict):
        raise ValueError(
            "experiment_result must be a dictionary."
        )

    if experiment_result.get("status") != "completed":
        raise ValueError(
            "Only completed experiments can be recorded."
        )

    comparison = experiment_result["comparison"]

    return {
        "study": experiment_result["study"],
        "experiment_version": comparison["experiment_version"],
        "scenario_version": comparison["scenario_version"],
        "random_seed": comparison["random_seed"],
        "equal_test_budget": comparison["equal_test_budget"],
        "test_budget": comparison["test_budget"],

        "static": comparison["static"],
        "adaptive": comparison["adaptive"],
        "difference": comparison["difference"],
    }