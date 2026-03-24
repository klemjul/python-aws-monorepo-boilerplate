"""Greeter utility - builds personalised greeting messages."""


def greet(name: str) -> str:
    """Return a greeting message for the given name.

    Args:
        name: The name to greet.

    Returns:
        A greeting string such as "Hello, Alice!".
    """
    return f"Hello, {name}!"
