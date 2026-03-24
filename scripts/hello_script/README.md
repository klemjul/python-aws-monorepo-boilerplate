# hello-script

> Example Hello World script demonstrating the `scripts/` monorepo pattern.

## Overview

`hello-script` is a simple CLI script that prints a personalised greeting. It serves as a template for adding new Python scripts to this monorepo.

## Usage

```bash
# Run directly with uv
uv run --directory scripts/hello_script hello-script
uv run --directory scripts/hello_script hello-script --name Alice
```
