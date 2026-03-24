"""Pre-commit hook that validates the current git branch name."""

import re
import subprocess
import sys

BRANCH_PATTERN = re.compile(
    r"^(main|master|develop|(feature|bugfix|hotfix|release|chore|docs|refactor|test)/[a-z0-9][a-z0-9._/-]*)$"
)

USAGE_HINT = (
    "Branch names must match one of the following patterns:\n"
    "  main | master | develop\n"
    "  feature/<description>\n"
    "  bugfix/<description>\n"
    "  hotfix/<description>\n"
    "  release/<description>\n"
    "  chore/<description>\n"
    "  docs/<description>\n"
    "  refactor/<description>\n"
    "  test/<description>\n"
    "\n"
    "Where <description> uses only lowercase letters, digits, hyphens, dots,"
    " or slashes."
)


def get_branch_name() -> str:
    """Return the name of the currently checked-out git branch."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def is_valid_branch_name(branch: str) -> bool:
    """Return True when *branch* matches the project naming convention."""
    return bool(BRANCH_PATTERN.match(branch))


def main() -> None:
    """Entry point for the check-branch-name pre-commit hook."""
    try:
        branch = get_branch_name()
    except subprocess.CalledProcessError as exc:
        print(
            f"check-branch-name: failed to determine branch name: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not is_valid_branch_name(branch):
        print(
            f"check-branch-name: invalid branch name '{branch}'\n\n{USAGE_HINT}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"check-branch-name: '{branch}' OK")


if __name__ == "__main__":
    main()
