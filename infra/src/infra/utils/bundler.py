"""Local CDK bundler utilities."""

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import warnings

import aws_cdk as cdk
import jsii

# infra/src/infra/utils/bundler.py is four levels below the repo root
REPO_ROOT: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)


def deps_hash(lambda_dir: str) -> str:
    """Compute a hash from the lambda's ``pyproject.toml`` only.

    The layer is rebuilt only when ``pyproject.toml`` changes, not when the
    handler source code changes.
    """
    hasher = hashlib.sha256()
    filepath = os.path.join(lambda_dir, "pyproject.toml")
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            hasher.update(f.read())
    return hasher.hexdigest()[:32]


@jsii.implements(cdk.ILocalBundling)
class DepsBundler:
    """Local bundler that installs a Python package's runtime deps with uv.

    Uses ``uv export --no-emit-project`` to resolve only the transitive runtime
    dependencies (not the project package itself) and installs them into
    ``output_dir/python`` so the directory can be used as a Lambda Layer source.

    Raises ``RuntimeError`` if ``uv`` is not on PATH or if any uv command
    fails — there is no Docker fallback.
    """

    def __init__(self, source_dir: str) -> None:
        """Initialise the bundler.

        Args:
            source_dir: Absolute path to the package directory whose runtime
                deps should be bundled (e.g. the lambda directory).
        """
        self._source_dir = source_dir

    def try_bundle(self, output_dir: str, _options: cdk.BundlingOptions) -> bool:
        """Install runtime deps of ``source_dir`` into ``output_dir/python``.
        The jsii runtime calls this with two positional arguments.
        Args:
            output_dir: Destination directory for the bundled layer contents.
            _options: CDK bundling options passed by the jsii runtime (unused).

        Returns:
            True if bundling succeeded.

        Raises:
            RuntimeError: If uv is not found or any uv command fails.
        """
        if sys.platform != "linux":
            warnings.warn(
                f"DepsBundler is running on {sys.platform!r}, not Linux. "
                "Lambda layers require Linux-compatible wheels — the bundled "
                "layer may be incompatible with AWS Lambda.",
                RuntimeWarning,
                stacklevel=2,
            )

        python_dir = os.path.join(output_dir, "python")
        os.makedirs(python_dir, exist_ok=True)

        uv_bin = shutil.which("uv")
        if not uv_bin:
            raise RuntimeError(
                "DepsBundler: 'uv' not found on PATH. "
                "Install uv (https://docs.astral.sh/uv/getting-started/installation/) "
                "to bundle Lambda dependencies."
            )

        # Read the package name from pyproject.toml so we can pass it to
        # `uv export --package <name>`.
        with open(os.path.join(self._source_dir, "pyproject.toml"), "rb") as f:
            package_name: str = tomllib.load(f)["project"]["name"]

        # Step 1: Export transitive dependencies, excluding the project package
        # itself (--no-emit-project).  This ensures the lambda handler code is
        # not duplicated in the layer (it is deployed separately via
        # Code.from_asset(.../src)).
        export_result = subprocess.run(  # noqa: S603
            [
                uv_bin,
                "export",
                f"--package={package_name}",
                "--no-emit-project",
                "--no-hashes",
                "--frozen",
                "--no-dev",
                "--color=never",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if export_result.returncode != 0:
            raise RuntimeError(
                f"uv export failed (exit {export_result.returncode}):\n"
                f"{export_result.stderr}"
            )

        # Separate requirements into external packages and local workspace
        # packages.  uv exports workspace members as editable entries
        # (e.g. ``-e ./packages/shared``); these cannot be installed into a
        # target directory with --editable, so we convert them to absolute
        # paths for a regular (non-editable) install.
        _pkg_line_re = re.compile(r"^[A-Za-z0-9_]")
        external_lines: list[str] = []
        workspace_paths: list[str] = []
        for line in export_result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("-e "):
                # ``-e ./packages/shared`` → absolute path for non-editable install
                rel_path = stripped[3:].strip()
                workspace_paths.append(os.path.join(REPO_ROOT, rel_path))
            elif _pkg_line_re.match(line):
                external_lines.append(line)

        requirements = "\n".join(external_lines)
        if requirements:
            requirements += "\n"

        # Skip install step if there is nothing to install.
        if not requirements and not workspace_paths:
            return True

        # Build the install command; workspace paths are added as direct
        # (non-editable) installs alongside the requirements file.
        install_cmd = [
            uv_bin,
            "pip",
            "install",
        ]
        install_cmd.extend(workspace_paths)

        req_path: str | None = None
        try:
            if requirements:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False
                ) as req_file:
                    req_file.write(requirements)
                    req_path = req_file.name
                install_cmd += ["-r", req_path]

            install_cmd += [
                "-t",
                python_dir,
                "--no-cache-dir",
                "--python",
                sys.executable,
            ]

            install_result = subprocess.run(  # noqa: S603
                install_cmd,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            if req_path is not None:
                os.unlink(req_path)

        if install_result.returncode != 0:
            raise RuntimeError(
                f"uv pip install failed (exit {install_result.returncode}):\n"
                f"{install_result.stderr}"
            )

        return True
