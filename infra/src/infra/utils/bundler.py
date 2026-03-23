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


def _hash_directory(hasher: "hashlib._Hash", directory: str) -> None:
    """Hash all files in a directory recursively in sorted order for determinism.

    Args:
        hasher: A :mod:`hashlib` hash object to update in place.
        directory: Path to the directory to hash.
    """
    for dirpath, dirnames, filenames in os.walk(directory):
        dirnames.sort()
        for filename in sorted(filenames):
            filepath = os.path.join(dirpath, filename)
            hasher.update(filepath.encode())
            with open(filepath, "rb") as f:
                hasher.update(f.read())


def deps_hash(lambda_dir: str) -> str:
    """Compute a hash from the lambda's ``pyproject.toml`` and any workspace
    package sources that ``DepsBundler`` vendors into the layer.

    The layer is rebuilt when either:
    - the lambda's ``pyproject.toml`` changes (dependency version bump), or
    - the source code of any vendored workspace package changes.
    """
    hasher = hashlib.sha256()
    filepath = os.path.join(lambda_dir, "pyproject.toml")
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            content = f.read()
        hasher.update(content)

        # Also hash workspace package sources so layer is rebuilt when they change.
        try:
            data = tomllib.loads(content.decode())
            sources = data.get("tool", {}).get("uv", {}).get("sources", {})
            for pkg_name, source in sources.items():
                if isinstance(source, dict) and source.get("workspace"):
                    pkg_src = os.path.join(REPO_ROOT, "packages", pkg_name, "src")
                    if os.path.isdir(pkg_src):
                        _hash_directory(hasher, pkg_src)
        except (tomllib.TOMLDecodeError, OSError):
            pass

    return hasher.hexdigest()[:32]


@jsii.implements(cdk.ILocalBundling)
class DepsBundler:
    """Local bundler that installs a Python package's runtime deps with uv.

    Uses ``uv export --no-emit-project`` to resolve only the transitive runtime
    dependencies (not the project package itself) and installs them into
    ``output_dir/python`` so the directory can be used as a Lambda Layer source.

    Raises ``RuntimeError`` if ``uv`` is not on PATH or if any uv command fails.
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
                "Lambda layers require Linux-compatible wheels. "
                "The bundled layer may be incompatible with AWS Lambda.",
                RuntimeWarning,
                stacklevel=2,
            )

        python_dir = os.path.join(output_dir, "python")
        os.makedirs(python_dir, exist_ok=True)

        uv_bin = shutil.which("uv")
        if not uv_bin:
            raise RuntimeError("DepsBundler: 'uv' not found on PATH. ")

        # Read the package name from pyproject.toml so we can pass it to
        # `uv export --package <name>`.
        with open(os.path.join(self._source_dir, "pyproject.toml"), "rb") as f:
            package_name: str = tomllib.load(f)["project"]["name"]

        # Export dependencies, excluding the project package itself (--no-emit-project)
        # This ensures the lambda handler code is not duplicated in the layer
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

        # Separate requirements into external packages and local workspace packages.
        _pkg_line_re = re.compile(r"^[A-Za-z0-9_]")
        external_lines: list[str] = []
        workspace_paths: list[str] = []
        for line in export_result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("-e "):
                # Handle editable/local dependencies (e.g. -e ./packages/shared)
                rel_path = stripped[3:].strip()
                workspace_paths.append(os.path.join(REPO_ROOT, rel_path))
            elif _pkg_line_re.match(line):
                # Handle external dependencies
                external_lines.append(line)

        requirements = "\n".join(external_lines)
        if requirements:
            requirements += "\n"

        if not requirements and not workspace_paths:
            return True

        # For workspace packages, copy their src/ into the target python_dir.
        for ws_path in workspace_paths:
            src_dir = os.path.join(ws_path, "src")
            if os.path.isdir(src_dir):
                for entry in os.listdir(src_dir):
                    src = os.path.join(src_dir, entry)
                    dst = os.path.join(python_dir, entry)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)

        if not requirements:
            return True

        # Build the install command for external packages only.
        install_cmd = [
            uv_bin,
            "pip",
            "install",
        ]

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

            # for external dependencies, use pip to install into the layer's python_dir
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
