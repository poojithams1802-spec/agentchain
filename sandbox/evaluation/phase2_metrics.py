from collections import defaultdict


PHASE2_CONDITIONS = {
    "rule_based_fixed_mitigation",
    "llm_recommendation_only",
    "level3_proposed",
    "wrong_control",
}


def calculate_phase2_metrics(results):
    if not isinstance(results, list):
        raise ValueError("results must be a list")

    grouped = defaultdict(list)

    for result in results:
        condition = result.get("condition")

        if condition not in PHASE2_CONDITIONS:
            raise ValueError(
                f"Unknown Phase 2 condition: {condition}"
            )

        grouped[condition].append(result)

    metrics = {}

    for condition in PHASE2_CONDITIONS:
        condition_results = grouped.get(condition, [])

        if not condition_results:
            continue

        total = len(condition_results)

        # --------------------------------------------------
        # Mitigation selection
        # --------------------------------------------------

        selection_correct = sum(
            1
            for result in condition_results
            if result.get("selection_correct") is True
        )

        mitigation_selection_accuracy = (
            selection_correct / total
        )

        # --------------------------------------------------
        # Mitigation application
        # --------------------------------------------------

        # Recommendation-only deliberately does not apply
        # the selected mitigation, so application success
        # is not applicable for this condition.
        if condition == "llm_recommendation_only":
            mitigation_application_success = None

        else:
            application_attempts = sum(
                1
                for result in condition_results
                if result.get("mitigation_control") is not None
            )

            successful_applications = sum(
                1
                for result in condition_results
                if result.get("mitigation_applied") is True
            )

            mitigation_application_success = (
                successful_applications / application_attempts
                if application_attempts
                else None
            )

        # --------------------------------------------------
        # Attack success before mitigation
        # --------------------------------------------------

        before_values = [
            result.get("attack_success_before")
            for result in condition_results
            if result.get("attack_success_before") is not None
        ]

        attack_success_before = (
            sum(
                1
                for value in before_values
                if value is True
            )
            / len(before_values)
            if before_values
            else None
        )

        # --------------------------------------------------
        # Attack success after mitigation
        # --------------------------------------------------

        after_values = [
            result.get("attack_success_after")
            for result in condition_results
            if result.get("attack_success_after") is not None
        ]

        attack_success_after = (
            sum(
                1
                for value in after_values
                if value is True
            )
            / len(after_values)
            if after_values
            else None
        )

        # --------------------------------------------------
        # Chain disruption
        # --------------------------------------------------

        disruption_values = [
            result.get("chain_disrupted")
            for result in condition_results
            if result.get("attack_success_before") is not None
        ]

        chain_disruption_rate = (
            sum(
                1
                for value in disruption_values
                if value is True
            )
            / len(disruption_values)
            if disruption_values
            else None
        )

        # --------------------------------------------------
        # Mitigation validation
        # --------------------------------------------------

        # Recommendation-only does not perform replay or
        # mitigation validation, so this metric is N/A.
        if condition == "llm_recommendation_only":
            mitigation_validation_rate = None

        else:
            validation_values = [
                result.get("mitigation_validation")
                for result in condition_results
                if result.get("mitigation_control") is not None
            ]

            mitigation_validation_rate = (
                sum(
                    1
                    for value in validation_values
                    if value is True
                )
                / len(validation_values)
                if validation_values
                else None
            )

        # --------------------------------------------------
        # Residual vulnerable steps
        # --------------------------------------------------

        residual_steps = []

        for result in condition_results:
            residual_steps.extend(
                result.get(
                    "residual_vulnerable_steps",
                    []
                )
            )

        # --------------------------------------------------
        # LLM metrics
        # --------------------------------------------------

        llm_calls = sum(
            result.get("llm_calls", 0)
            for result in condition_results
        )

        # --------------------------------------------------
        # Final condition metrics
        # --------------------------------------------------

        metrics[condition] = {
            "experiment_count": total,
            "mitigation_selection_accuracy":
                mitigation_selection_accuracy,
            "mitigation_application_success":
                mitigation_application_success,
            "attack_success_rate_before":
                attack_success_before,
            "attack_success_rate_after":
                attack_success_after,
            "chain_disruption_rate":
                chain_disruption_rate,
            "mitigation_validation_rate":
                mitigation_validation_rate,
            "residual_vulnerable_steps":
                residual_steps,
            "llm_calls":
                llm_calls,
        }

    return metrics