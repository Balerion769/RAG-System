"""Unexecuted security scanner probe; this branch must never be merged."""


def security_probe() -> object:
    """Contain a deliberate tainted eval sink for the scanner smoke check."""
    user_expression = input("Expression: ")
    return eval(user_expression)
