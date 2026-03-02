# Code Walkthrough Notes

## Goal
Create a showboat walkthrough.md that explains the entire experiments repository in a linear, code-inclusive tour.

## Repository Overview
8 experiments covering:
1. cli-tools-pattern - Python package with CLI entry points
2. jsonforms-pydantic-demo (docs) - Showboat + Rodney documentation
3. llm-classification-app - Streamlit + FastAPI + Vertex AI classification
4. posit_connect_static_tool_test - Static HTML + FastAPI proxy
5. pydantic-jsonforms-demo - Pydantic → JSON Schema → React forms
6. readme-summaries-setup - GitHub Actions auto-README generation
7. simonw-tools-exploration - Flat HTML utilities infrastructure
8. wos-fast5k-playwright - Playwright bulk export automation

## Showboat Plan
- Use `showboat init` to create the document
- Use `showboat note` for section intros and explanations
- Use `showboat exec bash` with cat/grep/sed/head to embed code snippets

## Key Insight
The repo is a collection of experiments, each showing a different pattern or tool integration. The walkthrough should be linear — explaining each experiment's purpose, then showing the key code that makes it work.
