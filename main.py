"""Backward-compatible FastAPI entrypoint.

The API implementation lives in `app.api.server`; this module keeps existing
commands such as `uvicorn main:app` working.
"""

from app.api.server import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.api.server:app", host="127.0.0.1", port=8000, reload=True)
