"""Tests for the hello script."""

import pytest
from hello_script.main import greet


def test_greet_default_name() -> None:
    assert greet("World") == "Hello, World!"


def test_greet_with_name() -> None:
    assert greet("Alice") == "Hello, Alice!"


@pytest.mark.parametrize("name", ["Bob", "Charlie", "Django"])
def test_greet_various_names(name: str) -> None:
    assert greet(name) == f"Hello, {name}!"


def test_greet_returns_string() -> None:
    result = greet("Test")
    assert isinstance(result, str)


def test_greet_empty_name() -> None:
    assert greet("") == "Hello, !"
