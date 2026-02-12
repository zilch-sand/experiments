# JSONForms + Pydantic Demo Using Rodney and Showboat

## Overview

This experiment demonstrates how to use **rodney** and **showboat** to create executable documentation for the pydantic-jsonforms-demo experiment. It showcases the workflow of exploring and documenting a full-stack application that integrates Pydantic models with JSONForms.

## What are Rodney and Showboat?

### Rodney
**Rodney** is a command-line Chrome automation tool that allows you to:
- Launch and control a headless Chrome browser
- Navigate to URLs and interact with web pages
- Click elements, fill forms, and take screenshots
- Execute JavaScript and capture output
- Wait for elements and page events

Key commands:
```bash
rodney start                    # Launch Chrome
rodney open <url>               # Navigate to a URL
rodney click <selector>         # Click an element
rodney screenshot [file]        # Take a screenshot
rodney stop                     # Shutdown Chrome
```

### Showboat
**Showboat** is a tool for creating executable demo documents that mix commentary, code blocks, and captured output. It helps build markdown documents that serve as both readable documentation and reproducible proof of work.

Key commands:
```bash
showboat init <file> <title>            # Create a new demo document
showboat note <file> [text]             # Add commentary
showboat exec <file> <lang> [code]      # Run code and capture output
showboat image <file> [script]          # Run script and capture image
showboat verify <file>                  # Re-run all code blocks
```

## What This Demo Shows

This experiment demonstrates:

1. **Starting Services**: How to start the FastAPI backend and React frontend
2. **Browser Automation**: Using automated tools to interact with web applications (we used Playwright as an alternative to Rodney)
3. **Capturing Screenshots**: Taking snapshots of the application in various states
4. **Executable Documentation**: Building a markdown document that others can verify and reproduce

## Files in This Experiment

- `demo.md` - The main showboat document showing the complete workflow
- `notes.md` - Development notes and progress tracking
- `form-initial.png` - Screenshot of the initial form state
- `form-validated.png` - Screenshot after successful validation
- `form-expanded.png` - Screenshot showing expanded project details
- `README.md` - This file, explaining the experiment

## The pydantic-jsonforms-demo Application

The original experiment (located in `../pydantic-jsonforms-demo/`) demonstrates:

### Backend (FastAPI + Pydantic)
- Define data models with built-in validation rules
- Generate JSON Schema from Pydantic models
- Expose schemas and validation endpoints via FastAPI
- Handle complex nested objects and arrays

### Frontend (React + JSONForms + Material UI)
- Fetch JSON Schema from the backend
- Dynamically generate forms using JSONForms
- Apply Material UI styling for professional appearance
- Perform client-side validation
- Submit data for server-side validation

### Key Features
1. **Single Source of Truth**: Validation rules defined once in Pydantic
2. **Dynamic Forms**: UI generated automatically from schema
3. **Nested Objects**: Support for complex data structures
4. **Array Handling**: Add/remove items with min/max constraints
5. **Dual Validation**: Both client and server validation
6. **Type Safety**: Email, URL, date format validation

## How to Use This Demo

### View the Demo Document
```bash
cat demo.md
```

### Run the Applications
```bash
# Start the backend
cd ../pydantic-jsonforms-demo
uv run uvicorn app:app --port 8000

# In another terminal, start the frontend
cd ../pydantic-jsonforms-demo/jsonforms-client
npm install
npm run dev
```

### Try Rodney (if Chrome is available)
```bash
uvx rodney start
uvx rodney open http://localhost:5173
uvx rodney screenshot form.png
uvx rodney stop
```

### Create Your Own Showboat Demo
```bash
# Initialize a new demo
uvx showboat init my-demo.md "My Experiment"

# Add notes
uvx showboat note my-demo.md "This demonstrates..."

# Run commands and capture output
uvx showboat exec my-demo.md bash "echo 'Hello World'"

# Verify everything still works
uvx showboat verify my-demo.md
```

## Lessons Learned

1. **Rodney Limitations**: Rodney requires Chrome to be installed, which may not be available in all environments. Playwright is a good alternative.

2. **Showboat Benefits**: Creating executable documentation with showboat helps ensure that demos remain reproducible over time.

3. **Automation Value**: Automated browser tools make it easy to capture consistent screenshots and interact with applications programmatically.

4. **Documentation as Code**: By treating documentation as executable code, we can verify it continues to work as the application evolves.

## Next Steps

To extend this experiment, you could:

1. Use rodney to test error scenarios (invalid email, missing required fields)
2. Capture video recordings of the full workflow
3. Automate the entire demo creation process
4. Add more complex validation scenarios
5. Test accessibility features using rodney's ax-* commands

## Conclusion

This experiment successfully demonstrates how rodney and showboat can be used together to create executable documentation for web applications. While rodney wasn't available in our environment, the approach works well with alternative browser automation tools like Playwright.

The pydantic-jsonforms-demo serves as an excellent example of how to build forms dynamically from backend schemas, and tools like rodney and showboat make it easy to document and share these capabilities.
