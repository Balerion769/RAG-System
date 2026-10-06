"""Unexecuted security scanner probe; this branch must never be merged."""


def security_probe() -> str:
    """Return input as text without interpreting it as executable code."""
    user_expression = input("Expression: ")
    return user_expression
