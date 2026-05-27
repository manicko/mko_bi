"""Formula parsing utilities for data transformations.

This module provides functions to parse simple formulas into Polars expressions.
Supports binary arithmetic operators (+, -, *, /) between column names and numeric literals.
"""

import logging
import re

import polars as pl

logger = logging.getLogger(__name__)


def _is_numeric_literal(token: str) -> bool:
    """Check if token is a numeric literal (int or float, including negative).

    Args:
        token: Token string to check.

    Returns:
        True if token represents a numeric literal, False otherwise.
    """
    try:
        float(token)
        return True
    except ValueError:
        return False


def _parse_formula(formula: str) -> pl.Expr:
    """Parse simple formula into Polars expression.

    Supports binary arithmetic operators (+, -, *, /) between column names
    and numeric literals.

    Supported syntax
    ----------------
    - Single column: ``"revenue"`` → ``pl.col("revenue")``
    - Single literal: ``"100"`` → ``pl.lit(100)``
    - Binary op: ``"revenue / cost"`` → ``pl.col("revenue") / pl.col("cost")``
    - Chained: ``"a + b - c"`` → left-to-right evaluation
    - Numeric literals: ``"revenue * 100"`` → ``pl.col("revenue") * pl.lit(100)``

    Known limitations
    -----------------
    - **No parentheses** – ``"(a + b) * c"`` will not group as expected.
    - **No operator precedence** – all operations evaluate strictly
      left-to-right (e.g. ``"a + b * c"`` means ``(a + b) * c``, not
      ``a + (b * c)``).
    - **Column names** must match ``[a-zA-Z_][a-zA-Z0-9_]*``; names with
      spaces or special characters are not supported.
    - **No unary operators** – expressions like ``"-value"`` are invalid.

    Args:
        formula: Formula string containing column names, operators, and/or
            numeric literals, e.g. ``"revenue / cost"`` or ``"revenue * 100"``.

    Returns:
        pl.Expr: Polars expression representing the formula.

    Raises:
        ValueError: If the formula is empty, malformed, or contains
            unsupported operators.
    """
    if not formula or not formula.strip():
        raise ValueError("Formula must not be empty")

    tokens = re.split(r'([+\-*/])', formula)
    tokens = [t.strip() for t in tokens if t.strip()]

    # Handle negative numbers: merge '-' followed immediately by a number into a negative literal
    # e.g., ['100', '-', '5'] becomes ['100', '-', '-5'] when '-' at position 2 is followed by a number
    # But only when the previous token was an operator (meaning we're expecting an operand)
    _OPERATORS = {"+", "-", "*", "/"}
    merged: list[str] = []
    i = 0
    while i < len(tokens):
        if (merged and
            merged[-1] in _OPERATORS and
            i + 1 < len(tokens) and
            tokens[i] == "-" and
            _is_numeric_literal(tokens[i + 1])):
            # This is a negative number literal after an operator
            merged.append("-" + tokens[i + 1])
            i += 2
        else:
            merged.append(tokens[i])
            i += 1

    tokens = merged

    if not tokens:
        raise ValueError("Formula must not be empty")

    if len(tokens) == 1:
        token = tokens[0]
        if _is_numeric_literal(token):
            return pl.lit(float(token))
        # Validate that single token is a valid column name
        _VALID_COLUMN_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        if not _VALID_COLUMN_RE.match(token):
            raise ValueError(
                f"Invalid operand {token!r} in formula. Operands must be column names matching "
                f"[a-zA-Z_][a-zA-Z0-9_]* or numeric literals"
            )
        return pl.col(token)

    # Validate token pattern: operand, op, operand, op, operand, ...
    _validate_formula_tokens(tokens)

    def _token_to_expr(token: str) -> pl.Expr:
        """Convert token to appropriate Polars expression."""
        if _is_numeric_literal(token):
            return pl.lit(float(token))
        return pl.col(token)

    expr = _token_to_expr(tokens[0])
    i = 1
    while i < len(tokens):
        op = tokens[i]
        next_token = tokens[i + 1]
        next_expr = _token_to_expr(next_token)

        if op == "+":
            expr = expr + next_expr
        elif op == "-":
            expr = expr - next_expr
        elif op == "*":
            expr = expr * next_expr
        elif op == "/":
            expr = expr / next_expr
        else:
            raise ValueError(
                f"Unsupported operator '{op}' in formula: {formula!r}"
            )
        i += 2

    return expr


def _validate_formula_tokens(tokens: list[str]) -> None:
    """Validate that formula tokens follow the expected pattern.

    Expects alternating operands (column names or numeric literals) and binary
    operators, starting and ending with an operand:
    ``operand op operand op operand ...``.

    Args:
        tokens: List of parsed formula tokens.

    Raises:
        ValueError: If the token pattern is invalid.
    """
    _VALID_COLUMN_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    _OPERATORS = {"+", "-", "*", "/"}

    for idx, token in enumerate(tokens):
        if idx % 2 == 0:
            # Even indices must be column names or numeric literals
            if not _is_numeric_literal(token) and not _VALID_COLUMN_RE.match(token):
                raise ValueError(
                    f"Invalid operand {token!r} at position {idx} "
                    f"in formula. Operands must be column names matching "
                    f"[a-zA-Z_][a-zA-Z0-9_]* or numeric literals"
                )
        else:
            # Odd indices must be operators
            if token not in _OPERATORS:
                raise ValueError(
                    f"Expected operator at position {idx}, got {token!r}"
                )

    # Token count must be odd (starts and ends with operand)
    if len(tokens) % 2 == 0:
        raise ValueError(
            "Malformed formula: formula must end with an operand, "
            "not an operator"
        )