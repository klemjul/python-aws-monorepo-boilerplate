"""Unit tests for infra/infra/utils/bundler.py (DepsBundler)."""

import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import aws_cdk as cdk
import pytest
from infra.utils.bundler import DepsBundler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_PYPROJECT = b'[project]\nname = "hello"\n'
_FAKE_REQUIREMENTS = "-e ./packages/shared\naws-lambda-powertools==3.26.0\n"


def _mock_subprocess_run(export_rc: int = 0, install_rc: int = 0) -> MagicMock:
    """Return a side_effect callable that yields successive subprocess results."""
    export_mock = MagicMock()
    export_mock.returncode = export_rc
    export_mock.stdout = _FAKE_REQUIREMENTS
    export_mock.stderr = "export error"

    install_mock = MagicMock()
    install_mock.returncode = install_rc

    results = iter([export_mock, install_mock])

    def _run(cmd: list[str], **kwargs: object) -> MagicMock:
        return next(results)

    return MagicMock(side_effect=_run)


# ---------------------------------------------------------------------------
# try_bundle - uv not found
# ---------------------------------------------------------------------------


def test_try_bundle_raises_when_uv_missing(tmp_path: Path) -> None:
    """try_bundle must raise RuntimeError immediately when uv is not on PATH."""
    bundler = DepsBundler("/fake/source")
    with patch("infra.utils.bundler.shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="'uv' not found"):
            bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))


def test_try_bundle_creates_python_dir_even_when_uv_missing(tmp_path: Path) -> None:
    """The python/ subdirectory is created before the uv check."""
    bundler = DepsBundler("/fake/source")
    with patch("infra.utils.bundler.shutil.which", return_value=None):
        with pytest.raises(RuntimeError):
            bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    assert os.path.isdir(os.path.join(str(tmp_path), "python"))


# ---------------------------------------------------------------------------
# try_bundle - uv found, subprocess outcomes
# ---------------------------------------------------------------------------


def test_try_bundle_returns_true_on_success(tmp_path: Path) -> None:
    """try_bundle returns True when both uv commands exit with code 0."""
    bundler = DepsBundler("/fake/source")
    mock_run = _mock_subprocess_run(export_rc=0, install_rc=0)
    with (
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", mock_run),
        patch("builtins.open", mock_open(read_data=_FAKE_PYPROJECT)),
        patch("infra.utils.bundler.os.unlink"),
    ):
        result = bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    assert result is True


def test_try_bundle_raises_on_export_failure(tmp_path: Path) -> None:
    """try_bundle raises RuntimeError when uv export exits with non-zero code."""
    bundler = DepsBundler("/fake/source")
    mock_run = _mock_subprocess_run(export_rc=1, install_rc=0)
    with (
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", mock_run),
        patch("builtins.open", mock_open(read_data=_FAKE_PYPROJECT)),
        patch("infra.utils.bundler.os.unlink"),
    ):
        with pytest.raises(RuntimeError, match="uv export failed"):
            bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))


def test_try_bundle_raises_on_install_failure(tmp_path: Path) -> None:
    """try_bundle raises RuntimeError when uv pip install exits with non-zero code."""
    bundler = DepsBundler("/fake/source")
    mock_run = _mock_subprocess_run(export_rc=0, install_rc=1)
    with (
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", mock_run),
        patch("builtins.open", mock_open(read_data=_FAKE_PYPROJECT)),
        patch("infra.utils.bundler.os.unlink"),
    ):
        with pytest.raises(RuntimeError, match="uv pip install failed"):
            bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))


# ---------------------------------------------------------------------------
# try_bundle - command construction
# ---------------------------------------------------------------------------


def test_try_bundle_export_uses_package_name(tmp_path: Path) -> None:
    """uv export must be called with the package name read from pyproject.toml."""
    bundler = DepsBundler("/fake/source")
    mock_run = _mock_subprocess_run()
    with (
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", mock_run),
        patch("builtins.open", mock_open(read_data=_FAKE_PYPROJECT)),
        patch("infra.utils.bundler.os.unlink"),
    ):
        bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    # The first call is uv export
    first_call_cmd = mock_run.call_args_list[0][0][0]
    assert any("--package=hello" in arg for arg in first_call_cmd)


def test_try_bundle_export_uses_no_emit_project(tmp_path: Path) -> None:
    """uv export must include --no-emit-project to skip the lambda package itself."""
    bundler = DepsBundler("/fake/source")
    mock_run = _mock_subprocess_run()
    with (
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", mock_run),
        patch("builtins.open", mock_open(read_data=_FAKE_PYPROJECT)),
        patch("infra.utils.bundler.os.unlink"),
    ):
        bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    first_call_cmd = mock_run.call_args_list[0][0][0]
    assert "--no-emit-project" in first_call_cmd


def test_try_bundle_install_uses_requirements_file(tmp_path: Path) -> None:
    """uv pip install must be called with -r <requirements_file>."""
    bundler = DepsBundler("/fake/source")
    mock_run = _mock_subprocess_run()
    with (
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", mock_run),
        patch("builtins.open", mock_open(read_data=_FAKE_PYPROJECT)),
        patch("infra.utils.bundler.os.unlink"),
    ):
        bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    install_cmd = mock_run.call_args_list[1][0][0]
    assert "-r" in install_cmd


def test_try_bundle_installs_into_python_subdir(tmp_path: Path) -> None:
    """uv pip install target (-t) must be <output_dir>/python."""
    bundler = DepsBundler("/fake/source")
    mock_run = _mock_subprocess_run()
    with (
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", mock_run),
        patch("builtins.open", mock_open(read_data=_FAKE_PYPROJECT)),
        patch("infra.utils.bundler.os.unlink"),
    ):
        bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    install_cmd = mock_run.call_args_list[1][0][0]
    expected_python_dir = os.path.join(str(tmp_path), "python")
    assert expected_python_dir in install_cmd


def test_try_bundle_runs_from_repo_root(tmp_path: Path) -> None:
    """Both subprocess.run calls must use cwd=REPO_ROOT."""
    from infra.utils.bundler import REPO_ROOT

    bundler = DepsBundler("/fake/source")
    mock_run = _mock_subprocess_run()
    with (
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", mock_run),
        patch("builtins.open", mock_open(read_data=_FAKE_PYPROJECT)),
        patch("infra.utils.bundler.os.unlink"),
    ):
        bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))
    for call in mock_run.call_args_list:
        assert call[1].get("cwd") == REPO_ROOT


# ---------------------------------------------------------------------------
# try_bundle - exception handling
# ---------------------------------------------------------------------------


def test_try_bundle_propagates_oserror(tmp_path: Path) -> None:
    """If subprocess.run raises OSError the exception bubbles up."""
    bundler = DepsBundler("/fake/source")
    with (
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", side_effect=OSError("exec failed")),
        patch("builtins.open", mock_open(read_data=_FAKE_PYPROJECT)),
        patch("infra.utils.bundler.os.unlink"),
    ):
        with pytest.raises(OSError, match="exec failed"):
            bundler.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))


# ---------------------------------------------------------------------------
# DepsBundler.__init__
# ---------------------------------------------------------------------------


def test_different_bundlers_use_their_own_source_dirs(tmp_path: Path) -> None:
    """Two bundler instances with different source dirs must use their own paths."""
    mock_run = _mock_subprocess_run()

    bundler_a = DepsBundler("/source/a")
    bundler_b = DepsBundler("/source/b")

    with (
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", mock_run),
        patch("builtins.open", mock_open(read_data=_FAKE_PYPROJECT)),
        patch("infra.utils.bundler.os.unlink"),
    ):
        bundler_a.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))

    # Reset mocks for the second bundler invocation
    mock_run2 = _mock_subprocess_run()
    with (
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", mock_run2),
        patch("builtins.open", mock_open(read_data=_FAKE_PYPROJECT)),
        patch("infra.utils.bundler.os.unlink"),
    ):
        bundler_b.try_bundle(str(tmp_path), MagicMock(spec=cdk.BundlingOptions))


# ---------------------------------------------------------------------------
# REPO_ROOT sanity check
# ---------------------------------------------------------------------------


def test_repo_root_points_to_existing_directory() -> None:
    """REPO_ROOT must resolve to a real directory containing pyproject.toml."""
    from infra.utils.bundler import REPO_ROOT

    assert os.path.isdir(REPO_ROOT)
    assert os.path.isfile(os.path.join(REPO_ROOT, "pyproject.toml"))
