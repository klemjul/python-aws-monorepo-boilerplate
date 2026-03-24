"""Local CDK bundler utilities."""

import glob
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


def gitignore_exclude_patterns() -> list[str]:
    """Return non-empty, non-comment lines from the root ``.gitignore``.

    The returned patterns can be passed directly to CDK ``exclude`` (together
    with ``ignore_mode=cdk.IgnoreMode.GIT``) or stripped of trailing slashes
    and forwarded to ``shutil.ignore_patterns``.

    Returns an empty list when the ``.gitignore`` file does not exist.
    """
    gitignore_path = os.path.join(REPO_ROOT, ".gitignore")
    patterns: list[str] = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path) as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    patterns.append(stripped)
    return patterns


def _hash_directory(hasher: "hashlib._Hash", dirpath: str) -> None:
    """Update *hasher* with the path and content of every file under *dirpath*.

    Files are visited in a deterministic (sorted) order so the hash is
    stable across runs and platforms.
    """
    for root, dirs, files in os.walk(dirpath):
        dirs.sort()
        for filename in sorted(files):
            filepath = os.path.join(root, filename)
            # Include relative path so renames change the hash.
            hasher.update(os.path.relpath(filepath, dirpath).encode())
            with open(filepath, "rb") as fh:
                hasher.update(fh.read())


def deps_hash(lambda_dir: str) -> str:
    """Compute a hash from the lambda's ``pyproject.toml`` and any workspace
    package sources that will be copied directly into the layer.

    The layer is rebuilt when either the lambda's ``pyproject.toml`` changes
    (external dependencies change) **or** when the source of a workspace
    package dependency changes.
    """
    hasher = hashlib.sha256()
    filepath = os.path.join(lambda_dir, "pyproject.toml")
    if not os.path.exists(filepath):
        return hasher.hexdigest()[:32]

    with open(filepath, "rb") as f:
        content = f.read()
    hasher.update(content)

    # Discover workspace package dependencies and include their sources in the
    # hash so that changes to those packages trigger a layer rebuild.
    toml_data = tomllib.loads(content.decode())
    uv_sources = toml_data.get("tool", {}).get("uv", {}).get("sources", {})
    workspace_pkg_names = {
        name for name, src in uv_sources.items() if src.get("workspace")
    }

    if workspace_pkg_names:
        root_pyproject = os.path.join(REPO_ROOT, "pyproject.toml")
        if os.path.exists(root_pyproject):
            with open(root_pyproject, "rb") as f:
                root_data = tomllib.load(f)
            member_patterns: list[str] = (
                root_data.get("tool", {})
                .get("uv", {})
                .get("workspace", {})
                .get("members", [])
            )
            for pattern in member_patterns:
                for member_dir in sorted(glob.glob(os.path.join(REPO_ROOT, pattern))):
                    member_pyproject = os.path.join(member_dir, "pyproject.toml")
                    if not os.path.exists(member_pyproject):
                        continue
                    with open(member_pyproject, "rb") as f:
                        member_data = tomllib.load(f)
                    member_name = member_data.get("project", {}).get("name")
                    if member_name not in workspace_pkg_names:
                        continue
                    src_dir = os.path.join(member_dir, "src")
                    if os.path.isdir(src_dir):
                        _hash_directory(hasher, src_dir)

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
        self._gitignore_patterns = gitignore_exclude_patterns()

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
        # Strip trailing slashes from gitignore patterns so shutil.ignore_patterns
        # can match directory entries by name.
        _gitignore = [p.rstrip("/") for p in self._gitignore_patterns]
        _ignore_fn = shutil.ignore_patterns(*_gitignore)
        for ws_path in workspace_paths:
            src_dir = os.path.join(ws_path, "src")
            if os.path.isdir(src_dir):
                shutil.copytree(
                    src_dir,
                    python_dir,
                    dirs_exist_ok=True,
                    ignore=_ignore_fn,
                )

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
