"""Tests for the shared greeter module."""

import pytest
from shared.greeter import greet


def test_greet_default_name() -> None:
    assert greet("World") == "Hello, World!"


def test_greet_with_name() -> None:
    assert greet("Alice") == "Hello, Alice!"


@pytest.mark.parametrize("name", ["Bob", "Charlie", "Django"])
def test_greet_various_names(name: str) -> None:
    assert greet(name) == f"Hello, {name}!"


def test_greet_returns_string() -> None:
    assert isinstance(greet("Test"), str)
