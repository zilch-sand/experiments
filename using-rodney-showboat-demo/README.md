# Using Rodney and Showboat to Demonstrate the Pydantic JSONForms Experiment

## Overview

This experiment explores two powerful command-line tools - **rodney** and **showboat** - and demonstrates their use with the pydantic-jsonforms-demo project. The primary deliverable is an executable demo document created with showboat that shows how the pydantic-jsonforms experiment works.

## What Are These Tools?

### Rodney

[Rodney](https://github.com/go-rod/rod) is a Chrome automation tool with a clean command-line interface. Key features:

- **Browser Lifecycle**: Start/stop/status commands for Chrome
- **Navigation**: Open URLs, navigate history, reload pages
- **Interaction**: Click elements, fill forms, submit data
- **Extraction**: Get page content, screenshots, PDFs
- **Waiting**: Wait for elements, page load, network idle
- **Accessibility**: Query accessibility tree and nodes

Example commands:
```bash
rodney start                    # Launch Chrome
rodney open http://example.com  # Navigate to URL
rodney screenshot page.png      # Take screenshot
rodney click "button.submit"    # Click an element
```

### Showboat

[Showboat](https://github.com/simonw/showboat) creates executable demo documents that mix commentary with code execution. Key features:

- **Executable Documentation**: Code blocks that run and capture output
- **Verification**: Re-run all commands to ensure demos still work
- **Extraction**: Generate the commands needed to recreate a document
- **Multiple Languages**: Support for bash, python, and more
- **Image Support**: Capture and embed screenshots

Example commands:
```bash
showboat init demo.md "My Demo"           # Create new demo
showboat note demo.md "Commentary text"   # Add narrative
showboat exec demo.md bash "ls -la"       # Run command, capture output
showboat verify demo.md                   # Re-run and verify
```

## The Demo

The main deliverable is `demo.md` - a showboat document that:

1. **Explains the tools** - What rodney and showboat are and how they work
2. **Demonstrates the pydantic-jsonforms-demo** - Shows the FastAPI backend and React client in action
3. **Tests the API endpoints** - Validates the schema generation and validation logic
4. **Proves the work** - All commands are executable and outputs are captured

### Running the Demo

To see the demo:
```bash
cat demo.md
```

To verify all the commands still work:
```bash
# Start the backend first
cd ../pydantic-jsonforms-demo
uv run uvicorn app:app --reload --port 8000 &

# Then verify the demo
cd ../using-rodney-showboat-demo
showboat verify demo.md
```

## Key Findings

### Showboat Strengths
- Creates self-documenting, verifiable demos
- Perfect for proof-of-work and reproducible documentation
- Simple CLI makes it easy to build up demos incrementally
- The `verify` command ensures demos don't go stale

### Pydantic + JSONForms Integration
- JSON Schema is automatically generated from Pydantic models
- No duplication of validation rules needed
- Detailed error messages with field locations
- Validation rules (email format, string length, etc.) are reflected in the schema

### Rodney (Limited Testing)
- Provides a clean, simple CLI for browser automation
- Would complement showboat for visual demos
- Could not fully test due to environment constraints (browser installation issues)
- Would be valuable for automating UI testing and screenshots

## Pydantic JSONForms Demo Highlights

The experiment demonstrates:

1. **Schema Generation** - `GET /schema` returns JSON Schema from Pydantic models
2. **Server-side Validation** - `POST /validate` validates data using Pydantic
3. **Valid Data** - Returns validated data with success message
4. **Invalid Data** - Returns detailed errors with field paths and specific issues

Example error structure:
```json
{
  "type": "string_too_short",
  "loc": ["meta", "title"],
  "msg": "String should have at least 3 characters",
  "input": "Q2",
  "ctx": {"min_length": 3}
}
```

## Files

- **demo.md** - Main showboat executable demo document
- **notes.md** - Work log tracking the exploration
- **test-valid.json** - Valid test payload for validation
- **test-invalid.json** - Invalid test payload demonstrating error handling
- **README.md** - This file

## How to Use Showboat

The workflow demonstrated here:

```bash
# 1. Initialize a new demo
showboat init mydemo.md "Demo Title"

# 2. Add commentary
echo "Let's test the API" | showboat note mydemo.md

# 3. Execute commands and capture output
showboat exec mydemo.md bash "curl http://localhost:8000/schema"

# 4. Continue adding notes and commands
showboat note mydemo.md "The schema includes validation rules"

# 5. Verify everything still works
showboat verify mydemo.md
```

## Recommended Use Cases

### For Showboat
- Creating reproducible demos
- Documentation that stays current (via verify)
- Proof-of-work for development tasks
- Tutorial content with executable examples
- API testing documentation

### For Rodney
- Automated UI testing
- Taking screenshots for documentation
- Form filling and submission testing
- Accessibility tree inspection
- Browser-based integration tests

### Together
- Complete demos with both API and UI testing
- Visual documentation with screenshots
- End-to-end workflow demonstrations
- Automated documentation that includes browser interactions

## Related Projects

- [pydantic-jsonforms-demo](../pydantic-jsonforms-demo) - The experiment we're demonstrating
- [JSONForms](https://jsonforms.io/) - Dynamic form generation from JSON Schema
- [Pydantic](https://docs.pydantic.dev/) - Data validation using Python type annotations
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework

## Conclusion

Showboat proved to be an excellent tool for creating executable, verifiable documentation. It captures the entire workflow with both the commands and their outputs, making it easy to demonstrate and verify the pydantic-jsonforms experiment. While we couldn't fully explore rodney due to environment constraints, its potential for browser automation is clear and would complement showboat well for creating complete visual demos.

The pydantic-jsonforms integration demonstrates the power of defining validation rules once in Pydantic and automatically generating JSON Schema for use in dynamic forms, eliminating duplication and keeping validation logic consistent between server and client.
