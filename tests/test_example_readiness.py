"""Tests for the example readiness component."""


# @id TEST-EXAMPLE-001
# @verifies REQ-EXAMPLE-001
def test_TEST_EXAMPLE_001():
    from example_readiness import report_readiness

    readiness = report_readiness({"requirements": True, "design": True, "commands": False})

    assert readiness["status"] == "fail"
    assert readiness["missing"] == ["commands"]
