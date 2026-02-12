# Work Log: Using Rodney and Showboat

## Initial Setup
- Installed `uv` package manager to enable `uvx` commands
- Ran `uvx rodney --help` and `uvx showboat --help` to understand the tools
- Created experiment folder: `using-rodney-showboat-demo`
- Initialized showboat document with `showboat init`

## Understanding the Tools

### Rodney
- Chrome automation tool with a simple CLI interface
- Commands for browser control: start/stop, navigate, click, screenshot, etc.
- Requires Chrome/Chromium to be installed
- Could not fully test in this environment due to network constraints preventing browser installation

### Showboat
- Creates executable demo documents
- Mixes markdown commentary with executable code blocks
- Captures command output automatically
- Supports verification to ensure demos remain valid over time
- Very useful for creating reproducible documentation

## Demonstrating the Pydantic JSONForms Experiment

### Backend (FastAPI)
- Started the FastAPI server: `uv run uvicorn app:app --reload --port 8000`
- Server exposes:
  - `GET /schema` - Returns JSON Schema generated from Pydantic models
  - `POST /validate` - Validates incoming JSON against Pydantic models

### Frontend (React + JSONForms)
- Set up the React client in `pydantic-jsonforms-demo/jsonforms-client`
- Ran `npm install` to install dependencies
- Started Vite dev server: `npm run dev` on port 5173
- Client fetches schema from API and renders form using JSONForms

### Testing with Showboat
- Used `showboat exec` to capture API responses
- Tested schema endpoint - shows complete JSON Schema with validation rules
- Tested validation with valid data - returned success message
- Tested validation with invalid data - returned detailed error messages

## Key Insights

1. **Showboat is excellent for creating executable documentation**
   - Each code block is executable and its output is captured
   - Makes it easy to demonstrate a workflow step-by-step
   - The document itself becomes proof of work

2. **Pydantic's automatic JSON Schema generation is powerful**
   - Define validation rules once in Python
   - Schema automatically includes: types, required fields, formats, constraints
   - No need to maintain separate validation rules

3. **JSONForms uses the schema for dynamic form rendering**
   - Reads the JSON Schema to understand data structure
   - Generates appropriate form controls
   - Validates against the same schema

4. **Rodney would be useful for UI testing**
   - Could automate interactions with the JSONForms client
   - Take screenshots of the form in different states
   - Verify form behavior programmatically
   - Not fully demonstrated due to environment constraints

## Files Created
- `demo.md` - Showboat executable demo document
- `notes.md` - This work log
- `test-valid.json` - Valid test payload
- `test-invalid.json` - Invalid test payload

## Next Steps
To expand this demo:
- Add more test cases (edge cases, boundary conditions)
- Demonstrate the UI schema customization
- Show cross-field validation examples
- Create a version with actual browser automation using rodney (in local environment)
