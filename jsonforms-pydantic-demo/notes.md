# Notes

## Goal
Use rodney and showboat to create a demonstration of how to use the jsonforms-pydantic experiment.

## Progress - Initial Attempt
- Installed uv package manager
- Ran `uvx rodney --help` - learned it's a Chrome automation tool from command line
- Ran `uvx showboat --help` - learned it's a tool for creating executable demo documents
- Explored the pydantic-jsonforms-demo folder which contains:
  - FastAPI app with Pydantic models for portfolio management
  - JSONForms client using React + MUI
  - Validation logic integrated with Pydantic
- Created new experiment folder: jsonforms-pydantic-demo
- Attempted to use rodney but Chrome wasn't available
- Used Playwright as a workaround to capture screenshots

## Progress - Second Attempt (After Repo Settings Update)
- User updated repo settings to enable rodney/showboat properly
- Recreated demo.md using proper showboat workflow
- Successfully used rodney to:
  - Start headless Chrome browser
  - Navigate to http://localhost:5173
  - Take initial screenshot
  - Click validation button using JavaScript
  - Take post-validation screenshot
  - Expand project details
  - Take expanded view screenshot
  - Stop Chrome cleanly
- All commands properly captured in showboat executable document
- Screenshots integrated into markdown
- Demo is now reproducible using `uvx showboat verify demo.md`
