# README summary generation setup

## How the summaries work

The top-level `README.md` contains a `cog` block that walks the repo directories, reads each project README, and (if a cached `_summary.md` is missing) calls the `llm` CLI with the model identifier `github/gpt-4.1` to generate a short summary. That cog block is executed by the GitHub Actions workflow, which runs `cog -r -P README.md` and then commits any updated README and `_summary.md` files back to the repo. The workflow provides the `GITHUB_TOKEN` environment variable to the `cog` step, which is the token the `llm` command uses for GitHub Models access in CI. This means summaries are generated automatically on pushes to `main` using GitHub Actions. See the root README and workflow for the exact commands and model reference.【F:README.md†L18-L172】【F:.github/workflows/update-readme.yml†L1-L49】

## Do I need an API key?

In GitHub Actions, no extra API key is required beyond the built-in `GITHUB_TOKEN` because the workflow already provides that token to the `cog` step. Locally, you will need a GitHub token with GitHub Models access configured for the `llm-github-models` plugin, since the cog script uses `llm -m github/gpt-4.1`. The repo includes `llm` and `llm-github-models` in `requirements.txt` to support that flow. 【F:.github/workflows/update-readme.yml†L33-L49】【F:requirements.txt†L1-L3】【F:README.md†L103-L107】

## Do I need a GitHub Copilot account?

The setup references GitHub Models (via `llm-github-models`) rather than Copilot-specific tooling. Access is tied to GitHub Models permissions on the account or token being used; the repo itself does not mention Copilot as a requirement. 【F:requirements.txt†L1-L3】【F:README.md†L103-L107】

## What do I need to set up?

- For GitHub Actions: nothing beyond enabling Actions in the repo. The workflow already installs dependencies and runs `cog` with `GITHUB_TOKEN`. 【F:.github/workflows/update-readme.yml†L1-L49】
- For local runs: install the requirements, authenticate `llm` with a GitHub token that has GitHub Models access, and run `cog -r -P README.md`. The commands are in the README and workflow. 【F:requirements.txt†L1-L3】【F:README.md†L18-L172】【F:.github/workflows/update-readme.yml†L29-L38】
