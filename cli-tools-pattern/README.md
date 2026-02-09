# Python CLI tools pattern (multiple entry points)

This folder demonstrates how to define **two CLI tools** in a single Python package and how to install them so they are available in another project without prefixing commands with `uv run`.

## Package layout

```
cli-tools-pattern/
├── pyproject.toml
└── src/
    └── cli_tools_demo/
        ├── __init__.py
        └── cli.py
```

## Entry points definition

`pyproject.toml` uses the `[project.scripts]` table to map command names to Python callables:

```toml
[project.scripts]
hello-world = "cli_tools_demo.cli:hello_world"
goodbye-world = "cli_tools_demo.cli:goodbye_world"
```

Each callable in `cli_tools_demo/cli.py` is a separate CLI tool.

## Installing in another project (recommended)

From another project, install this package into its virtual environment. Once installed, the commands are available on the shell path **without** `uv run`:

```bash
# In your other project
python -m venv .venv
source .venv/bin/activate
pip install -e /path/to/cli-tools-pattern

hello-world --name "Ada"
goodbye-world --name "Grace"
```

### Using `uv` (still works without `uv run`)

If you use `uv`, you can still install into the environment and run the commands directly once the environment is activated:

```bash
# In your other project
uv venv
source .venv/bin/activate
uv pip install -e /path/to/cli-tools-pattern

hello-world --name "Ada"
goodbye-world --name "Grace"
```

`uv run` is only necessary when you do **not** activate the environment. Once it is activated, the console scripts are on PATH.

## Local development quick check

From this folder:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

hello-world
hello-world --name "Taylor"
goodbye-world --name "Jordan"
```

## Notes

- Use `[project.scripts]` for multiple entry points; each entry becomes its own command.
- A single module (`cli.py`) can host multiple tools, or you can split each tool into a separate module.
