def calculate_research_metrics(dataset):
    """
    Calculate descriptive research metrics from the
    recorded experiment dataset.

    Metrics are calculated separately for static
    and adaptive experiments.

    Phase 2 additionally calculates mitigation and
    before/after replay metrics.
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
            "llm_calls": 0,

            # Phase 2
            "mitigation_selections": 0,
            "successful_mitigation_applications": 0,
            "attack_success_before": 0,
            "attack_success_after": 0,
            "disrupted_chains": 0,
            "mitigation_validations": 0,
            "residual_vulnerable_steps": 0,
            "mitigation_selection_accuracy": 0.0,
            "mitigation_application_success": 0.0,
            "attack_success_rate_before": 0.0,
            "attack_success_rate_after": 0.0,
            "chain_disruption_rate": 0.0,
            "mitigation_validation_rate": 0.0
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
            "llm_calls": 0,

            # Phase 2
            "mitigation_selections": 0,
            "successful_mitigation_applications": 0,
            "attack_success_before": 0,
            "attack_success_after": 0,
            "disrupted_chains": 0,
            "mitigation_validations": 0,
            "residual_vulnerable_steps": 0,
            "mitigation_selection_accuracy": 0.0,
            "mitigation_application_success": 0.0,
            "attack_success_rate_before": 0.0,
            "attack_success_rate_after": 0.0,
            "chain_disruption_rate": 0.0,
            "mitigation_validation_rate": 0.0
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

        # --------------------------------------------------
        # Phase 2 mitigation metrics
        # --------------------------------------------------

        mitigation_selected = experiment.get(
            "mitigation_selected"
        )

        mitigation_control = experiment.get(
            "mitigation_control"
        )

        mitigation_applied = experiment.get(
            "mitigation_applied",
            False
        )

        attack_success_before = experiment.get(
            "attack_success_before"
        )

        attack_success_after = experiment.get(
            "attack_success_after"
        )

        chain_disrupted = experiment.get(
            "chain_disrupted",
            False
        )

        residual_steps = experiment.get(
            "residual_vulnerable_steps",
            []
        )

        mitigation_validation = experiment.get(
            "mitigation_validation",
            False
        )

        # Only count mitigation experiments when
        # mitigation data is actually present.
        if mitigation_control is not None:
            metrics[mode]["mitigation_selections"] += 1

            if mitigation_selected is True:
                metrics[mode]["mitigation_selection_accuracy"] += 1

            if mitigation_applied is True:
                metrics[mode][
                    "successful_mitigation_applications"
                ] += 1

            if attack_success_before is True:
                metrics[mode]["attack_success_before"] += 1

            if attack_success_after is True:
                metrics[mode]["attack_success_after"] += 1

            if chain_disrupted is True:
                metrics[mode]["disrupted_chains"] += 1

            if mitigation_validation is True:
                metrics[mode]["mitigation_validations"] += 1

            metrics[mode]["residual_vulnerable_steps"] += len(
                residual_steps
            )

    # ------------------------------------------------------
    # Calculate averages and rates
    # ------------------------------------------------------

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

        mitigation_count = metrics[mode][
            "mitigation_selections"
        ]

        if mitigation_count > 0:

            metrics[mode]["mitigation_selection_accuracy"] = (
                metrics[mode]["mitigation_selection_accuracy"]
                / mitigation_count
            )

            metrics[mode]["mitigation_application_success"] = (
                metrics[mode][
                    "successful_mitigation_applications"
                ]
                / mitigation_count
            )

            metrics[mode]["attack_success_rate_before"] = (
                metrics[mode]["attack_success_before"]
                / mitigation_count
            )

            metrics[mode]["attack_success_rate_after"] = (
                metrics[mode]["attack_success_after"]
                / mitigation_count
            )

            metrics[mode]["chain_disruption_rate"] = (
                metrics[mode]["disrupted_chains"]
                / mitigation_count
            )

            metrics[mode]["mitigation_validation_rate"] = (
                metrics[mode]["mitigation_validations"]
                / mitigation_count
            )

    return metrics