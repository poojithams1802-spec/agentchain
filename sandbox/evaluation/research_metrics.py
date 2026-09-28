def calculate_research_metrics(dataset):
    """
    Calculate descriptive research metrics from the
    recorded experiment dataset.

    Metrics are calculated separately for static
    and adaptive experiments.
    """

    if not isinstance(dataset, dict):
        raise ValueError("dataset must be a dictionary")

    experiments = dataset.get("experiments", [])

    metrics = {
        "static": {
            "experiments": 0,
            "total_tests": 0,
            "total_findings": 0,
            "valid_findings": 0,
            "candidate_chains": 0,
            "validated_chains": 0,
            "average_chain_length": 0.0,
            "validation_rate": 0.0,
            "execution_count": 0,
            "llm_calls": 0
        },
        "adaptive": {
            "experiments": 0,
            "total_tests": 0,
            "total_findings": 0,
            "valid_findings": 0,
            "candidate_chains": 0,
            "validated_chains": 0,
            "average_chain_length": 0.0,
            "validation_rate": 0.0,
            "execution_count": 0,
            "llm_calls": 0
        }
    }

    chain_lengths = {
        "static": [],
        "adaptive": []
    }

    validation_rates = {
        "static": [],
        "adaptive": []
    }

    for experiment in experiments:

        mode = experiment.get("mode")

        if mode not in {"static", "adaptive"}:
            continue

        metrics[mode]["experiments"] += 1

        metrics[mode]["total_tests"] += len(
            experiment.get("executed_tests", [])
        )

        findings = experiment.get("findings", [])

        metrics[mode]["total_findings"] += len(findings)

        metrics[mode]["valid_findings"] += len(
        experiment.get("findings", [])
        )
        metrics[mode]["candidate_chains"] += len(
            experiment.get("candidate_chains", [])
        )

        metrics[mode]["validated_chains"] += len(
            experiment.get("validated_chains", [])
        )

        metrics[mode]["execution_count"] += experiment.get(
            "execution_count",
            0
        )

        metrics[mode]["llm_calls"] += experiment.get(
            "llm_calls",
            0
        )

        chain_lengths[mode].append(
            experiment.get(
                "average_chain_length",
                0.0
            )
        )

        validation_rates[mode].append(
            experiment.get(
                "validation_rate",
                0.0
            )
        )

    for mode in ("static", "adaptive"):

        if chain_lengths[mode]:
            metrics[mode]["average_chain_length"] = (
                sum(chain_lengths[mode])
                / len(chain_lengths[mode])
            )

        if validation_rates[mode]:
            metrics[mode]["validation_rate"] = (
                sum(validation_rates[mode])
                / len(validation_rates[mode])
            )

    return metrics