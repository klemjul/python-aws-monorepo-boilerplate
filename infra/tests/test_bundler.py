"""Unit tests for infra/utils/bundler.py (DepsBundler)."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import aws_cdk as cdk
import pytest
from utils.bundler import DepsBundler

# ---------------------------------------------------------------------------
# try_bundle - uv not found
# ---------------------------------------------------------------------------


def test_try_bundle_returns_false_when_uv_missing(tmp_path: Path) -> None:
    """try_bundle must return False immediately when uv is not on PATH."""
    bundler = DepsBundler("/fake/source")
    with patch("utils.bundler.shutil.which", return_value=None):
        result = bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    assert result is False


def test_try_bundle_creates_python_dir_even_when_uv_missing(tmp_path: Path) -> None:
    """The python/ subdirectory is created before the uv check."""
    bundler = DepsBundler("/fake/source")
    with patch("utils.bundler.shutil.which", return_value=None):
        bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    assert os.path.isdir(os.path.join(str(tmp_path), "python"))


# ---------------------------------------------------------------------------
# try_bundle - uv found, subprocess outcomes
# ---------------------------------------------------------------------------


def test_try_bundle_returns_true_on_success(tmp_path: Path) -> None:
    """try_bundle returns True when uv exits with code 0."""
    bundler = DepsBundler("/fake/source")
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("utils.bundler.subprocess.run", return_value=mock_result) as mock_run,
    ):
        result = bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    assert result is True
    mock_run.assert_called_once()


def test_try_bundle_returns_false_on_subprocess_failure(tmp_path: Path) -> None:
    """try_bundle returns False when uv exits with a non-zero code."""
    bundler = DepsBundler("/fake/source")
    mock_result = MagicMock()
    mock_result.returncode = 1
    with (
        patch("utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("utils.bundler.subprocess.run", return_value=mock_result),
    ):
        result = bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    assert result is False


# ---------------------------------------------------------------------------
# try_bundle - subprocess command construction
# ---------------------------------------------------------------------------


def test_try_bundle_passes_source_dir_to_uv(tmp_path: Path) -> None:
    """uv pip install must receive the bundler's source_dir as the install target."""
    source_dir = "/my/lambda"
    bundler = DepsBundler(source_dir)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("utils.bundler.subprocess.run", return_value=mock_result) as mock_run,
    ):
        bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    cmd = mock_run.call_args[0][0]
    assert source_dir in cmd


def test_try_bundle_installs_into_python_subdir(tmp_path: Path) -> None:
    """uv pip install target (-t) must be <output_dir>/python."""
    bundler = DepsBundler("/fake/source")
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("utils.bundler.subprocess.run", return_value=mock_result) as mock_run,
    ):
        bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    cmd = mock_run.call_args[0][0]
    expected_python_dir = os.path.join(str(tmp_path), "python")
    assert expected_python_dir in cmd


def test_try_bundle_runs_from_repo_root(tmp_path: Path) -> None:
    """subprocess.run must be called with cwd=REPO_ROOT."""
    from utils.bundler import REPO_ROOT

    bundler = DepsBundler("/fake/source")
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("utils.bundler.subprocess.run", return_value=mock_result) as mock_run,
    ):
        bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    assert mock_run.call_args[1]["cwd"] == REPO_ROOT


def test_try_bundle_uses_uv_pip_install_subcommand(tmp_path: Path) -> None:
    """Command must start with uv pip install."""
    bundler = DepsBundler("/fake/source")
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("utils.bundler.subprocess.run", return_value=mock_result) as mock_run,
    ):
        bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    cmd = mock_run.call_args[0][0]
    assert cmd[:3] == ["/usr/bin/uv", "pip", "install"]


# ---------------------------------------------------------------------------
# try_bundle - subprocess exception handling
# ---------------------------------------------------------------------------


def test_try_bundle_propagates_oserror(tmp_path: Path) -> None:
    """If subprocess.run raises OSError the exception bubbles up."""
    bundler = DepsBundler("/fake/source")
    with (
        patch("utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("utils.bundler.subprocess.run", side_effect=OSError("exec failed")),
    ):
        with pytest.raises(OSError, match="exec failed"):
            bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))


# ---------------------------------------------------------------------------
# DepsBundler.__init__ - behavioral tests via try_bundle
# ---------------------------------------------------------------------------


def test_bundler_source_dir_used_in_command(tmp_path: Path) -> None:
    """The source_dir passed to __init__ must appear in the uv install command."""
    source_dir = "/my/custom/source"
    bundler = DepsBundler(source_dir)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("utils.bundler.subprocess.run", return_value=mock_result) as mock_run,
    ):
        bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    assert source_dir in mock_run.call_args[0][0]


def test_different_bundlers_use_their_own_source_dirs(tmp_path: Path) -> None:
    """Two bundler instances with different source dirs must use their own paths."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    calls: list[list[str]] = []

    def capture_run(cmd: list[str], **kwargs: object) -> MagicMock:
        calls.append(cmd)
        return mock_result

    bundler_a = DepsBundler("/source/a")
    bundler_b = DepsBundler("/source/b")
    with (
        patch("utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("utils.bundler.subprocess.run", side_effect=capture_run),
    ):
        bundler_a.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
        bundler_b.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))

    assert "/source/a" in calls[0]
    assert "/source/b" in calls[1]


# ---------------------------------------------------------------------------
# REPO_ROOT sanity check
# ---------------------------------------------------------------------------


def test_repo_root_points_to_existing_directory() -> None:
    """REPO_ROOT must resolve to a real directory containing pyproject.toml."""
    from utils.bundler import REPO_ROOT

    assert os.path.isdir(REPO_ROOT)
    assert os.path.isfile(os.path.join(REPO_ROOT, "pyproject.toml"))


def test_subprocess_run_called_with_check_false(tmp_path: Path) -> None:
    """subprocess.run must be invoked with check=False (non-raising on failure)."""
    bundler = DepsBundler("/fake/source")
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("utils.bundler.subprocess.run", return_value=mock_result) as mock_run,
    ):
        bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    assert mock_run.call_args[1].get("check") is False
