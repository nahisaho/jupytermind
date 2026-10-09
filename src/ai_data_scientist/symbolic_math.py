"""AST-whitelist-sandboxed single-variable symbolic algebra via sympy."""

import ast
import keyword

import sympy
from sympy.parsing.sympy_parser import parse_expr

_OPERATIONS = {"solve", "differentiate", "integrate", "simplify"}

_ALLOWED_NODE_TYPES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.FloorDiv,
    ast.USub,
    ast.UAdd,
)

_ALLOWED_FUNCTIONS = {
    "sin",
    "cos",
    "tan",
    "asin",
    "acos",
    "atan",
    "sinh",
    "cosh",
    "tanh",
    "exp",
    "log",
    "sqrt",
    "Abs",
}


def _check_whitelist(expression: str) -> None:
    """Parse ``expression`` into an AST and reject anything outside the fixed whitelist."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(
            "expression: must be a valid single-variable algebraic expression"
        ) from exc

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODE_TYPES):
            raise ValueError("expression: must be a valid single-variable algebraic expression")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ValueError("expression: must be a valid single-variable algebraic expression")
        if isinstance(node, ast.Call):
            if node.keywords:
                raise ValueError("expression: must be a valid single-variable algebraic expression")
            if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCTIONS:
                raise ValueError("expression: must be a valid single-variable algebraic expression")


# @id CODE-AIDS-170
# @implements REQ-AIDS-115
# @design DES-AIDS-113
def symbolic_compute(operation: str, expression: str, variable: str = "x") -> dict:
    """Dispatch a whitelisted, single-variable symbolic-algebra operation via sympy."""
    if operation not in _OPERATIONS:
        raise ValueError("operation: must be one of solve, differentiate, integrate, simplify")
    if not isinstance(variable, str) or not variable.isidentifier() or keyword.iskeyword(variable):
        raise ValueError("variable: must be a valid Python identifier")

    _check_whitelist(expression)

    symbol = sympy.Symbol(variable)
    try:
        parsed = parse_expr(expression, local_dict={variable: symbol}, evaluate=True)
    except Exception as exc:
        raise ValueError(
            "expression: must be a valid single-variable algebraic expression"
        ) from exc

    free_symbol_names = {str(s) for s in parsed.free_symbols}
    if free_symbol_names - {variable}:
        raise ValueError("expression: must contain only the declared variable")

    if operation == "solve":
        roots = sympy.solve(parsed, symbol)
        result = [str(root) for root in roots]
    elif operation == "differentiate":
        result = str(sympy.diff(parsed, symbol))
    elif operation == "integrate":
        result = str(sympy.integrate(parsed, symbol))
    else:
        result = str(sympy.simplify(parsed))

    return {"result": result}
