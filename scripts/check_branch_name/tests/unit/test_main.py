"""Tests for the check-branch-name script."""

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest
from check_branch_name.main import get_branch_name, is_valid_branch_name, main

# ─── is_valid_branch_name ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "branch",
    [
        "main",
        "master",
        "develop",
        "feature/my-feature",
        "feature/123-fix-login",
        "bugfix/fix-crash",
        "hotfix/urgent-patch",
        "release/1.0.0",
        "chore/update-deps",
        "docs/update-readme",
        "refactor/clean-up",
        "test/add-unit-tests",
        "feature/scope/sub-feature",
    ],
)
def test_valid_branch_names(branch: str) -> None:
    assert is_valid_branch_name(branch) is True


@pytest.mark.parametrize(
    "branch",
    [
        "",
        "Feature/my-feature",
        "FEATURE/my-feature",
        "my-feature",
        "feature/",
        "feature/ leading-space",
        "feature/has space",
        "feature/Has-Upper",
        "unknown/my-branch",
        "HEAD",
    ],
)
def test_invalid_branch_names(branch: str) -> None:
    assert is_valid_branch_name(branch) is False


# ─── get_branch_name ──────────────────────────────────────────────────────────


def test_get_branch_name_returns_stripped_output() -> None:
    mock_result = MagicMock()
    mock_result.stdout = "feature/my-feature\n"
    with patch("subprocess.run", return_value=mock_result):
        assert get_branch_name() == "feature/my-feature"


def test_get_branch_name_raises_on_failure() -> None:
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(128, "git")):
        with pytest.raises(subprocess.CalledProcessError):
            get_branch_name()


# ─── main ─────────────────────────────────────────────────────────────────────


def test_main_valid_branch(capsys: pytest.CaptureFixture[str]) -> None:
    with patch(
        "check_branch_name.main.get_branch_name", return_value="feature/my-feature"
    ):
        main()
    captured = capsys.readouterr()
    assert "OK" in captured.out


def test_main_invalid_branch_exits_nonzero(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("check_branch_name.main.get_branch_name", return_value="my-feature"):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "invalid branch name" in captured.err


def test_main_git_failure_exits_nonzero(capsys: pytest.CaptureFixture[str]) -> None:
    with patch(
        "check_branch_name.main.get_branch_name",
        side_effect=subprocess.CalledProcessError(128, "git"),
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "failed to determine branch name" in captured.err


def test_main_uses_sys_argv(capsys: pytest.CaptureFixture[str]) -> None:
    sys.argv = ["check-branch-name"]
    with patch("check_branch_name.main.get_branch_name", return_value="main"):
        main()
    captured = capsys.readouterr()
    assert "OK" in captured.out
