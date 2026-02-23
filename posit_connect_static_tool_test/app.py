# app.py
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
import httpx
from pathlib import Path

app = FastAPI(title="Connect Proxy Test")

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "static" / "index.html"


@app.get("/")
async def index():
    if not HTML_FILE.exists():
        raise HTTPException(status_code=500, detail=f"HTML file not found: {HTML_FILE}")
    return FileResponse(HTML_FILE, media_type="text/html")


@app.get("/index.html")
async def index_html():
    return await index()

# Optional: keep this permissive for testing, then lock it down later.
ALLOWED_HOSTS = {
    "api.github.com",
    "httpbin.org",
    "raw.githubusercontent.com",
}

@app.get("/api/proxy")
async def proxy(url: str = Query(..., description="Absolute URL to fetch server-side")):
    # Basic validation
    try:
        u = httpx.URL(url)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid URL")

    if u.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Only http/https supported")

    host = (u.host or "").lower()
    if host not in ALLOWED_HOSTS:
        raise HTTPException(status_code=403, detail=f"Host not allowed: {host}")

    # Fetch server-side (CSP does not apply here)
    timeout = httpx.Timeout(20.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            r = await client.get(str(u), headers={"User-Agent": "connect-proxy-test/1.0"})
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Upstream request failed: {e!s}")

    # Return response with the upstream content-type if present
    content_type = r.headers.get("content-type", "text/plain; charset=utf-8")

    # Safety: cap response size to keep the demo from pulling huge bodies
    body = r.content
    max_bytes = 1_000_000
    if len(body) > max_bytes:
        body = body[:max_bytes]

    return Response(
        content=body,
        status_code=r.status_code,
        media_type=content_type.split(";")[0].strip(),
        headers={"X-Upstream-Status": str(r.status_code)},
    )