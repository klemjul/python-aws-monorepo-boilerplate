"""Local CDK bundler utilities."""

import os
import shutil
import subprocess
import sys
import tempfile
import tomllib

import aws_cdk as cdk
import jsii

# infra/infra/utils/bundler.py is three levels below the repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


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

        # Step 2: Install the exported requirements into the layer directory.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as req_file:
            req_file.write(export_result.stdout)
            req_path = req_file.name

        try:
            install_result = subprocess.run(  # noqa: S603
                [
                    uv_bin,
                    "pip",
                    "install",
                    "-r",
                    req_path,
                    "-t",
                    python_dir,
                    "--no-cache-dir",
                    "--python",
                    sys.executable,
                ],
                cwd=REPO_ROOT,
                check=False,
            )
        finally:
            os.unlink(req_path)

        if install_result.returncode != 0:
            raise RuntimeError(
                f"uv pip install failed (exit {install_result.returncode})"
            )

        return True
