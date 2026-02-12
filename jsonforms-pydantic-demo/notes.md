# Notes

## Goal
Use rodney and showboat to create a demonstration of how to use the jsonforms-pydantic experiment.

## Progress
- Installed uv package manager
- Ran `uvx rodney --help` - learned it's a Chrome automation tool from command line
- Ran `uvx showboat --help` - learned it's a tool for creating executable demo documents
- Explored the pydantic-jsonforms-demo folder which contains:
  - FastAPI app with Pydantic models for portfolio management
  - JSONForms client using React + MUI
  - Validation logic integrated with Pydantic
- Created new experiment folder: jsonforms-pydantic-demo
- Initialized showboat demo document

## Next Steps
1. Start the FastAPI backend from the pydantic-jsonforms-demo
2. Start the JSONForms client
3. Use rodney to automate browser interactions with the form
4. Capture screenshots and outputs using showboat
5. Create a comprehensive demo document showing the workflow

## Demonstration Created
- Started FastAPI backend on port 8000
- Started React + Vite frontend on port 5173
- Used Playwright (instead of Rodney due to Chrome availability) to interact with the application
- Captured initial form state screenshot
- Clicked "Validate with API" button to demonstrate validation
- Captured validation success screenshot
- Documented features and workflow in showboat demo.md
