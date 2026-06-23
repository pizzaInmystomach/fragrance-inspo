# Architecture

This project is organized around a lightweight FastAPI service plus retrieval
and AI service modules.

## Backend Layout

```text
app/
├── api/          # FastAPI routes and API request/response schemas
├── ai/           # LLM configuration, prompts, and model checks
├── retrieval/    # Baseline, hybrid, and shared retrieval logic
├── data_handler.py
├── ingest.py
├── schemas.py    # Dataset/storage schemas
└── search_engine.py
```

`main.py` is only a backward-compatible shim for older commands such as:

```bash
uvicorn main:app
```

Use this as the canonical API entrypoint for new scripts and deployments:

```bash
uvicorn app.api.server:app
```

## Supporting Folders

```text
data/           # Source/evaluation datasets used by retrievers and benchmarks
docs/licenses/  # Dataset and third-party dependency license reports
frontend/       # Next.js app
metrics/        # Benchmark and request metric outputs
scripts/        # One-off data prep, benchmark, and evaluation scripts
tests/manual/   # Manual smoke-test and example scripts
```

## Placement Rules

- API routes and DTOs belong in `app/api/`.
- Retrieval logic belongs in `app/retrieval/`.
- LLM/provider setup belongs in `app/ai/`.
- Repeatable utilities belong in `scripts/`.
- Manual experiments belong in `tests/manual/`.
- Generated benchmark outputs belong in `metrics/`.
- License reports and non-user-facing documentation belong in `docs/`.
