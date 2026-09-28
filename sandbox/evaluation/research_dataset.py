def create_research_dataset(experiments=None):
    """
    Create a collection of standardized research experiment results.
    """

    if experiments is None:
        experiments = []

    return {
        "experiments": experiments,
        "total_experiments": len(experiments)
    }


def add_experiment(dataset, experiment):
    """
    Add one standardized experiment result to the dataset.
    """

    if not isinstance(dataset, dict):
        raise ValueError("dataset must be a dictionary")

    if "experiments" not in dataset:
        raise ValueError(
            "dataset must contain an experiments list"
        )

    dataset["experiments"].append(experiment)
    dataset["total_experiments"] = len(
        dataset["experiments"]
    )

    return dataset