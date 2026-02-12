# Using Rodney and Showboat to Demonstrate the Pydantic JSONForms Experiment

*2026-02-12T11:50:23Z*

This demo explores two powerful command-line tools: **rodney** and **showboat**. Rodney provides Chrome automation capabilities, while showboat creates executable demo documents. We'll use them together to demonstrate the pydantic-jsonforms-demo experiment.

## What is Rodney?

Rodney is a command-line tool for Chrome automation. It provides a simple interface to:
- Launch and control headless Chrome
- Navigate pages and interact with elements
- Capture screenshots and PDFs
- Execute JavaScript
- Wait for page elements and events

## What is Showboat?

Showboat is a tool for creating executable demo documents. It allows you to:
- Mix markdown commentary with executable code blocks
- Capture command output automatically
- Verify that demos still work over time
- Create reproducible proof of work

The document you're reading right now is a showboat document!

## The Pydantic JSONForms Demo

The pydantic-jsonforms-demo experiment shows how to use Pydantic models as the single source of truth for data validation, automatically generating JSON Schema to power dynamic forms via JSONForms. It includes:

1. A FastAPI backend that exposes:
   - `GET /schema` - Returns the JSON Schema generated from Pydantic models
   - `POST /validate` - Validates form data using Pydantic
   
2. A React client that:
   - Fetches the schema from the API
   - Renders a dynamic form using JSONForms
   - Validates user input server-side

Let's set this up and interact with it using rodney!

## Step 1: Start the FastAPI Backend

First, let's start the FastAPI backend server that serves the JSON Schema and validation endpoint.

```bash
curl -s http://localhost:8000/schema | python3 -m json.tool | head -30
```

```output
{
    "$defs": {
        "PortfolioMeta": {
            "properties": {
                "title": {
                    "maxLength": 80,
                    "minLength": 3,
                    "title": "Title",
                    "type": "string"
                },
                "owner_email": {
                    "format": "email",
                    "title": "Owner Email",
                    "type": "string"
                },
                "created_on": {
                    "format": "date",
                    "title": "Created On",
                    "type": "string"
                },
                "visibility": {
                    "default": "private",
                    "enum": [
                        "private",
                        "team",
                        "public"
                    ],
                    "title": "Visibility",
                    "type": "string"
                }
```

The API is now running on port 8000 and serving the JSON Schema that was automatically generated from Pydantic models.

## Step 2: Set Up and Run the JSONForms Client

Next, let's set up the React client that uses JSONForms to render a dynamic form based on the schema.

The React client is now running on port 5173. It will fetch the schema from our API and render a dynamic form.

## Step 3: Use Rodney to Interact with the Application

Now we'll use rodney to launch Chrome, navigate to the application, and interact with it.

## Alternative: Direct API Testing

Since installing a browser in this environment has connectivity issues, let's demonstrate the API endpoints directly using curl.

### Testing the Schema Endpoint

The schema endpoint returns the JSON Schema auto-generated from the Pydantic models:

```bash
curl -s http://localhost:8000/schema | python3 -m json.tool
```

```output
{
    "$defs": {
        "PortfolioMeta": {
            "properties": {
                "title": {
                    "maxLength": 80,
                    "minLength": 3,
                    "title": "Title",
                    "type": "string"
                },
                "owner_email": {
                    "format": "email",
                    "title": "Owner Email",
                    "type": "string"
                },
                "created_on": {
                    "format": "date",
                    "title": "Created On",
                    "type": "string"
                },
                "visibility": {
                    "default": "private",
                    "enum": [
                        "private",
                        "team",
                        "public"
                    ],
                    "title": "Visibility",
                    "type": "string"
                }
            },
            "required": [
                "title",
                "owner_email"
            ],
            "title": "PortfolioMeta",
            "type": "object"
        },
        "Project": {
            "properties": {
                "meta": {
                    "$ref": "#/$defs/ProjectMeta"
                },
                "summary": {
                    "maxLength": 400,
                    "minLength": 10,
                    "title": "Summary",
                    "type": "string"
                },
                "contributors": {
                    "items": {
                        "type": "string"
                    },
                    "maxItems": 10,
                    "title": "Contributors",
                    "type": "array"
                }
            },
            "required": [
                "meta",
                "summary"
            ],
            "title": "Project",
            "type": "object"
        },
        "ProjectMeta": {
            "properties": {
                "name": {
                    "maxLength": 60,
                    "minLength": 3,
                    "title": "Name",
                    "type": "string"
                },
                "status": {
                    "enum": [
                        "planned",
                        "active",
                        "paused",
                        "completed"
                    ],
                    "title": "Status",
                    "type": "string"
                },
                "start_date": {
                    "format": "date",
                    "title": "Start Date",
                    "type": "string"
                },
                "end_date": {
                    "default": null,
                    "title": "End Date",
                    "format": "date",
                    "type": "string"
                },
                "budget_usd": {
                    "maximum": 5000000,
                    "minimum": 0,
                    "title": "Budget Usd",
                    "type": "number"
                },
                "repo_url": {
                    "default": null,
                    "title": "Repo Url",
                    "format": "uri",
                    "maxLength": 2083,
                    "minLength": 1,
                    "type": "string"
                },
                "tags": {
                    "items": {
                        "type": "string"
                    },
                    "maxItems": 6,
                    "title": "Tags",
                    "type": "array"
                }
            },
            "required": [
                "name",
                "status",
                "start_date",
                "budget_usd"
            ],
            "title": "ProjectMeta",
            "type": "object"
        }
    },
    "properties": {
        "meta": {
            "$ref": "#/$defs/PortfolioMeta"
        },
        "projects": {
            "items": {
                "$ref": "#/$defs/Project"
            },
            "maxItems": 6,
            "minItems": 1,
            "title": "Projects",
            "type": "array"
        }
    },
    "required": [
        "meta",
        "projects"
    ],
    "title": "Portfolio",
    "type": "object"
}
```

### Testing the Validation Endpoint

Now let's test the validation endpoint with valid data:

```bash
curl -s -X POST http://localhost:8000/validate -H 'Content-Type: application/json' -d @test-valid.json | python3 -m json.tool
```

```output
{
    "message": "Portfolio is valid",
    "portfolio": {
        "meta": {
            "title": "Q2 Portfolio",
            "owner_email": "owner@example.com",
            "created_on": "2024-06-01",
            "visibility": "team"
        },
        "projects": [
            {
                "meta": {
                    "name": "Analytics Revamp",
                    "status": "active",
                    "start_date": "2024-03-01",
                    "end_date": null,
                    "budget_usd": 250000.0,
                    "repo_url": "https://github.com/example/analytics",
                    "tags": [
                        "data",
                        "etl"
                    ]
                },
                "summary": "Modernize the analytics pipeline and dashboards.",
                "contributors": [
                    "Ada Lovelace",
                    "Grace Hopper"
                ]
            }
        ]
    }
}
```

### Testing Validation with Invalid Data

Let's test what happens when we submit invalid data (invalid email):

```bash
curl -s -X POST http://localhost:8000/validate -H 'Content-Type: application/json' -d @test-invalid.json | python3 -m json.tool
```

```output
{
    "detail": [
        {
            "type": "string_too_short",
            "loc": [
                "meta",
                "title"
            ],
            "msg": "String should have at least 3 characters",
            "input": "Q2",
            "ctx": {
                "min_length": 3
            },
            "url": "https://errors.pydantic.dev/2.12/v/string_too_short"
        },
        {
            "type": "value_error",
            "loc": [
                "meta",
                "owner_email"
            ],
            "msg": "value is not a valid email address: An email address must have an @-sign.",
            "input": "not-an-email",
            "ctx": {
                "reason": "An email address must have an @-sign."
            }
        },
        {
            "type": "string_too_short",
            "loc": [
                "projects",
                0,
                "summary"
            ],
            "msg": "String should have at least 10 characters",
            "input": "Too short",
            "ctx": {
                "min_length": 10
            },
            "url": "https://errors.pydantic.dev/2.12/v/string_too_short"
        }
    ]
}
```

## Key Findings

### About Showboat
- Showboat makes it easy to create executable documentation that mixes narrative with code execution
- All commands are captured with their output, making the document reproducible
- The document can be verified later to ensure it still works
- Perfect for creating demos and proof-of-work documentation

### About the Pydantic JSONForms Integration
- The JSON Schema is automatically generated from Pydantic models - no duplication needed
- Validation rules defined in Pydantic (email format, string length, etc.) are reflected in the schema
- The FastAPI backend uses the same Pydantic models for validation
- Invalid data returns detailed error messages with field locations and specific issues

### About Rodney
While we couldn't demonstrate rodney in this environment due to browser installation constraints, it provides:
- Simple CLI commands for Chrome automation
- Useful for testing web UIs programmatically
- Can capture screenshots and interact with page elements
- Would complement showboat for creating visual demos

## Verifying This Demo

You can verify this demo yourself by running:

```bash
showboat verify demo.md
```

This will re-execute all the code blocks and confirm the outputs still match.

