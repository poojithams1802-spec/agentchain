from planner import AdaptivePlanner
from schemas import PlannerInput


def test_phase3_chain_combination_catalog():
    planner = AdaptivePlanner()

    combinations = planner.get_phase3_chain_combinations()

    assert len(combinations) == 5

    chain_ids = {item["chain_id"] for item in combinations}

    assert chain_ids == {
        "CHAIN_A",
        "CHAIN_B",
        "CHAIN_C",
        "CHAIN_D",
        "CHAIN_E",
    }

    for combination in combinations:
        assert combination["chain_id"]
        assert combination["name"]
        assert isinstance(combination["steps"], list)
        assert isinstance(combination["dependencies"], dict)
        assert isinstance(combination["approved_tests"], list)


def test_phase3_chain_dependencies_are_valid():
    planner = AdaptivePlanner()

    combinations = planner.get_phase3_chain_combinations()

    for combination in combinations:
        steps = set(combination["steps"])

        for step, dependencies in combination["dependencies"].items():
            assert step in steps

            for dependency in dependencies:
                assert dependency in steps


def test_phase3_chain_combination_builder_uses_current_state():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        previous_tests=[
            "permission_test",
        ],
    )

    combinations = planner.build_chain_combinations(planner_input)

    assert isinstance(combinations, list)
    assert len(combinations) > 0

    for combination in combinations:
        assert "chain_id" in combination
        assert "name" in combination
        assert "steps" in combination
        assert "dependencies" in combination
        assert "approved_tests" in combination