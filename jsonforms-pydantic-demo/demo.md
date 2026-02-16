# JSONForms + Pydantic Integration Demo

*2026-02-16T00:42:36Z by Showboat 0.5.0*

This demo showcases a full-stack integration between Pydantic models and JSONForms. The backend uses FastAPI with Pydantic for data validation, and the frontend uses React with JSONForms to dynamically generate forms from JSON Schema.

We'll use **rodney** (CLI browser automation) and **showboat** (executable documentation) to demonstrate the application.

## Starting the Backend

First, let's start the FastAPI backend which provides JSON Schema and validation endpoints.

```bash
curl -s http://localhost:8000/schema | python3 -m json.tool | head -40
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
```

## Using Rodney for Browser Automation

Now let's use rodney to launch Chrome and interact with the application.

```bash
uvx rodney start
```

```output
[launcher.Browser]2026/02/16 00:44:10 Download: https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/1321438/chrome-linux.zip
[launcher.Browser]2026/02/16 00:44:10 Progress: 00%
[launcher.Browser]2026/02/16 00:44:11 Progress: 67%
[launcher.Browser]2026/02/16 00:44:11 Unzip: /home/runner/.cache/rod/browser/chromium-1321438
[launcher.Browser]2026/02/16 00:44:11 Progress: 00%
[launcher.Browser]2026/02/16 00:44:12 Progress: 23%
[launcher.Browser]2026/02/16 00:44:13 Progress: 42%
[launcher.Browser]2026/02/16 00:44:14 Progress: 77%
[launcher.Browser]2026/02/16 00:44:15 Downloaded: /home/runner/.cache/rod/browser/chromium-1321438
Chrome started (PID 3030)
Debug URL: ws://127.0.0.1:38521/devtools/browser/fad421de-1798-4c66-a95c-463314e05a47
```

```bash
uvx rodney open http://localhost:5173 && uvx rodney waitload
```

```output
Pydantic + JSONForms Portfolio
Page loaded
```

The application loads with example portfolio data.

![Initial Form State](form-initial.png)

```bash
uvx rodney js "Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Validate with API'))?.click()" && uvx rodney sleep 2
```

```output
null
```

After clicking the validation button, the form data is validated by the backend:

![Form Validation Success](form-validated.png)

```bash
uvx rodney js "document.querySelectorAll('button')[0].click()" && uvx rodney sleep 1
```

```output
null
```

Expanding a project reveals all nested fields:

![Expanded Project Form](form-expanded.png)

```bash
uvx rodney stop
```

```output
Chrome stopped
```

## Conclusion

This demo successfully demonstrated:
- Using **rodney** for automated browser interaction
- Using **showboat** to create executable documentation
- The integration between Pydantic models and JSONForms
- How JSON Schema is generated from Pydantic and used by JSONForms
- Client-side and server-side validation working together

The combination of rodney and showboat makes it easy to create reproducible demonstrations that can be verified later.

