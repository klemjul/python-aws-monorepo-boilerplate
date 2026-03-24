"""Hello script - prints a personalised greeting."""

import argparse


def greet(name: str) -> str:
    """Return a greeting message for the given name.

    Args:
        name: The name to greet.

    Returns:
        A greeting string such as "Hello, Alice!".
    """
    return f"Hello, {name}!"


def main() -> None:
    """Entry point for the hello script."""
    parser = argparse.ArgumentParser(description="Greet someone by name.")
    parser.add_argument(
        "--name",
        default="World",
        help="Name to greet (default: World)",
    )
    args = parser.parse_args()
    print(greet(args.name))


if __name__ == "__main__":
    main()
