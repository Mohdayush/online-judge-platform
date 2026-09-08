# CodeArena — Online Judge Platform

An asynchronous online-judge backend. The current foundation provides JWT authentication, role-based problem creation, a normalized submission model, and an explicit queue/worker boundary for safe code execution.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for interactive API documentation.

## Design decision

The API records a submission and returns `202 Accepted`; it must never execute user code in the web process. A later worker service will consume the submission from Redis and run it in a resource-constrained, network-disabled container.
