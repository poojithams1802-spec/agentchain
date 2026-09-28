def summarize_research_dataset(dataset):
    """
    Create descriptive research metrics grouped by experiment mode.

    Expected modes:
        static
        adaptive
    """

    if not isinstance(dataset, dict):
        raise ValueError("dataset must be a dictionary")

    experiments = dataset.get("experiments", [])

    summary = {
        "total_experiments": len(experiments),
        "static": {
            "experiments": 0,
            "total_tests": 0,
            "total_findings": 0,
            "total_candidate_chains": 0,
            "total_validated_chains": 0,
            "average_validation_rate": 0.0,
            "average_chain_length": 0.0
        },
        "adaptive": {
            "experiments": 0,
            "total_tests": 0,
            "total_findings": 0,
            "total_candidate_chains": 0,
            "total_validated_chains": 0,
            "average_validation_rate": 0.0,
            "average_chain_length": 0.0
        }
    }

    mode_rates = {
        "static": [],
        "adaptive": []
    }

    mode_chain_lengths = {
        "static": [],
        "adaptive": []
    }

    for experiment in experiments:

        mode = experiment.get("mode")

        if mode not in {"static", "adaptive"}:
            continue

        summary[mode]["experiments"] += 1

        summary[mode]["total_tests"] += len(
            experiment.get("executed_tests", [])
        )

        summary[mode]["total_findings"] += len(
            experiment.get("findings", [])
        )

        summary[mode]["total_candidate_chains"] += len(
            experiment.get("candidate_chains", [])
        )

        summary[mode]["total_validated_chains"] += len(
            experiment.get("validated_chains", [])
        )

        mode_rates[mode].append(
            experiment.get("validation_rate", 0.0)
        )

        mode_chain_lengths[mode].append(
            experiment.get("average_chain_length", 0.0)
        )

    for mode in ("static", "adaptive"):

        if mode_rates[mode]:
            summary[mode]["average_validation_rate"] = (
                sum(mode_rates[mode])
                / len(mode_rates[mode])
            )

        if mode_chain_lengths[mode]:
            summary[mode]["average_chain_length"] = (
                sum(mode_chain_lengths[mode])
                / len(mode_chain_lengths[mode])
            )

    return summary