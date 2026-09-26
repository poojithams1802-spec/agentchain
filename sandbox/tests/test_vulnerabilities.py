from sandbox.vulnerabilities import (
    run_v1_scenario,
    run_v2_scenario,
    run_v3_scenario,
)


def test_v1():
    result = run_v1_scenario()

    assert result["vulnerability_id"] == "V1"
    assert result["vulnerable"] is True

    print("\nV1:", result)


def test_v2():
    result = run_v2_scenario()

    assert result["vulnerability_id"] == "V2"
    assert result["vulnerable"] is True

    print("\nV2:", result)


def test_v3():
    result = run_v3_scenario()

    assert result["vulnerability_id"] == "V3"
    assert result["vulnerable"] is True

    print("\nV3:", result)


if __name__ == "__main__":
    test_v1()
    test_v2()
    test_v3()

    print("\nAll vulnerability scenarios passed.")