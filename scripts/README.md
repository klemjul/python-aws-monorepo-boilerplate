# scripts

Python scripts that run outside of AWS Lambda (e.g. one-off jobs, data migrations, local utilities).

Each script lives in its own sub-folder and follows the same monorepo conventions as `lambdas/` and `packages/`:

| Path | Purpose |
| --- | --- |
| `<name>/src/<pkg>/` | Script source code |
| `<name>/tests/` | Unit and integration tests |
| `<name>/pyproject.toml` | Package metadata and entry-point declaration |
| `<name>/README.md` | Script-specific documentation |

## Scripts

| Name | Description |
| --- | --- |
| [hello](hello/) | Example hello-world CLI script |
