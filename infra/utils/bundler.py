"""Local CDK bundler utilities."""

import os
import shutil
import subprocess
import sys

import aws_cdk as cdk
import jsii

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@jsii.implements(cdk.ILocalBundling)
class DepsBundler:
    """Local bundler that installs a Python package's runtime deps with uv.

    Installs the package located at ``source_dir`` (including all transitive
    runtime dependencies declared in its ``pyproject.toml``) into
    ``output_dir/python`` so the directory can be used as a Lambda Layer source.

    Used as the primary bundler when Docker is not available (e.g. in CI synth).
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
            True if bundling succeeded, False otherwise.
        """
        python_dir = os.path.join(output_dir, "python")
        os.makedirs(python_dir, exist_ok=True)

        uv_bin = shutil.which("uv")
        if not uv_bin:
            # uv is required so that workspace dependencies declared via
            # [tool.uv.sources] (e.g. shared = { workspace = true }) are
            # correctly resolved.  Without uv, fall back to Docker bundling.
            print("DepsBundler: 'uv' not found; skipping local bundling.")
            return False

        cmd: list[str] = [
            uv_bin,
            "pip",
            "install",
            self._source_dir,
            "-t",
            python_dir,
            "--no-cache-dir",
            "--quiet",
            "--python",
            sys.executable,
        ]

        # Run from REPO_ROOT so uv can resolve workspace dependencies declared
        # via [tool.uv.sources] (e.g. shared = { workspace = true }).
        result = subprocess.run(cmd, cwd=REPO_ROOT, check=False)  # noqa: S603
        return result.returncode == 0
