import pytest


# @id TEST-AIDS-432
# @verifies REQ-AIDS-115
def test_TEST_AIDS_432_solve_happy_path():
    from ai_data_scientist.symbolic_math import symbolic_compute

    result = symbolic_compute("solve", "x**2 - 4")
    assert result["result"] == ["-2", "2"]


# @id TEST-AIDS-433
# @verifies REQ-AIDS-115
def test_TEST_AIDS_433_differentiate_happy_path():
    from ai_data_scientist.symbolic_math import symbolic_compute

    result = symbolic_compute("differentiate", "x**3 + 2*x")
    assert result["result"] == "3*x**2 + 2"


# @id TEST-AIDS-434
# @verifies REQ-AIDS-115
def test_TEST_AIDS_434_integrate_happy_path():
    from ai_data_scientist.symbolic_math import symbolic_compute

    result = symbolic_compute("integrate", "2*x")
    assert result["result"] == "x**2"


# @id TEST-AIDS-435
# @verifies REQ-AIDS-115
def test_TEST_AIDS_435_simplify_happy_path():
    from ai_data_scientist.symbolic_math import symbolic_compute

    result = symbolic_compute("simplify", "(x**2 - 1)/(x - 1)")
    assert result["result"] == "x + 1"


# @id TEST-AIDS-436
# @verifies REQ-AIDS-115
def test_TEST_AIDS_436_invalid_operation_is_rejected():
    from ai_data_scientist.symbolic_math import symbolic_compute

    with pytest.raises(
        ValueError, match="must be one of solve, differentiate, integrate, simplify"
    ):
        symbolic_compute("factor", "x**2 - 4")


# @id TEST-AIDS-437
# @verifies REQ-AIDS-115
def test_TEST_AIDS_437_extra_free_symbol_is_rejected():
    from ai_data_scientist.symbolic_math import symbolic_compute

    with pytest.raises(ValueError, match="must contain only the declared variable"):
        symbolic_compute("solve", "x + y")


# @id TEST-AIDS-438
# @verifies REQ-AIDS-115
def test_TEST_AIDS_438_unparsable_expression_is_rejected():
    from ai_data_scientist.symbolic_math import symbolic_compute

    with pytest.raises(ValueError, match="must be a valid single-variable algebraic expression"):
        symbolic_compute("solve", "x +* 2")


# @id TEST-AIDS-439
# @verifies REQ-AIDS-115
def test_TEST_AIDS_439_subclasses_sandbox_escape_rejected_before_sympy(monkeypatch):
    import ai_data_scientist.symbolic_math as symbolic_math_module

    class _NeverReached:
        pass

    monkeypatch.setattr(symbolic_math_module, "parse_expr", lambda *a, **k: _NeverReached())

    with pytest.raises(ValueError, match="must be a valid single-variable algebraic expression"):
        symbolic_math_module.symbolic_compute("solve", "().__class__.__base__.__subclasses__()")


# @id TEST-AIDS-440
# @verifies REQ-AIDS-115
def test_TEST_AIDS_440_import_os_sandbox_escape_rejected_before_sympy(monkeypatch):
    import ai_data_scientist.symbolic_math as symbolic_math_module

    class _NeverReached:
        pass

    monkeypatch.setattr(symbolic_math_module, "parse_expr", lambda *a, **k: _NeverReached())

    with pytest.raises(ValueError, match="must be a valid single-variable algebraic expression"):
        symbolic_math_module.symbolic_compute("solve", '__import__("os").system("echo pwned")')


# @id TEST-AIDS-441
# @verifies REQ-AIDS-115
def test_TEST_AIDS_441_invalid_variable_identifier_is_rejected():
    from ai_data_scientist.symbolic_math import symbolic_compute

    with pytest.raises(ValueError, match="must be a valid Python identifier"):
        symbolic_compute("solve", "x**2 - 4", variable="123bad")


# @id TEST-AIDS-442
# @verifies REQ-AIDS-115
def test_TEST_AIDS_442_keyword_variable_is_rejected():
    from ai_data_scientist.symbolic_math import symbolic_compute

    with pytest.raises(ValueError, match="must be a valid Python identifier"):
        symbolic_compute("solve", "for - 4", variable="for")


# @id TEST-AIDS-443
# @verifies REQ-AIDS-115
def test_TEST_AIDS_443_disallowed_function_call_is_rejected():
    from ai_data_scientist.symbolic_math import symbolic_compute

    with pytest.raises(ValueError, match="must be a valid single-variable algebraic expression"):
        symbolic_compute("solve", "foo(x)")
