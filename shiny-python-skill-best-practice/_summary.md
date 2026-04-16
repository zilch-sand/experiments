Leveraging both hands-on testing and analysis of official documentation, this project developed a production-ready Claude Skill for Shiny for Python best practices, specifically targeting gaps in existing agent-oriented skills. The skill package, organized for Claude/agent execution, systematically covers architecture choices (Core vs Express), safe reactivity patterns (especially with mutable state), modular design for scalability, and pragmatic testing and deployment strategies—all tailored for recent Shiny Python releases. Validation included local installs, app scaffolding, CLI testing, and cross-referencing current release features. External guides (like [posit-dev/skills](https://github.com/posit-dev/skills)) and [Shiny for Python docs](https://shiny.posit.co/py/docs/) informed structure and advice.

Key findings:
- Python Shiny skills require explicit guidance for reactivity/mutability hazards, unlike R equivalents.
- Both Core and Express offer valid architectures—best practice is context-dependent.
- Version-specific features (AI-driven tools, OpenTelemetry, code input APIs) should inform recommendations.
