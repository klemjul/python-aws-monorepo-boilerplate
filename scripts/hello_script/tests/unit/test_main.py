"""Tests for the hello script CLI."""

import sys

import pytest


def test_main_default_name(capsys: pytest.CaptureFixture[str]) -> None:
    from hello_script.main import main

    sys.argv = ["hello-script"]
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "Hello, World!"


def test_main_with_name_argument(capsys: pytest.CaptureFixture[str]) -> None:
    from hello_script.main import main

    sys.argv = ["hello-script", "--name", "Alice"]
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "Hello, Alice!"


@pytest.mark.parametrize("name", ["Bob", "Charlie", "Django"])
def test_main_various_names(name: str, capsys: pytest.CaptureFixture[str]) -> None:
    from hello_script.main import main

    sys.argv = ["hello-script", "--name", name]
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == f"Hello, {name}!"
