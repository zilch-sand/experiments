Demonstrating how to package multiple command-line tools in one Python package, this project leverages the `[project.scripts]` section in `pyproject.toml` to create distinct shell commands that map to individual Python functions. By installing the package into a virtual environment (via pip or [uv](https://github.com/astral-sh/uv)), users gain direct access to each tool (e.g., `hello-world`, `goodbye-world`) without needing command prefixes. Each entry point is defined as a callable in a shared module, allowing flexible organization within the package. The approach streamlines CLI tool distribution and avoids manual invocation, making integration into other projects straightforward.

**Key takeaways:**
- Use `[project.scripts]` to define multiple commands from one package.
- Installing in a virtualenv exposes tools directly on the system PATH.
- Each CLI entry point can be implemented in a single file or split across modules.  
- [uv](https://github.com/astral-sh/uv) can simplify environment setup and installation.
