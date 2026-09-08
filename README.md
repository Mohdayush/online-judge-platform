# CodeArena — Online Judge Platform

An asynchronous online-judge backend. It provides JWT authentication, role-based problem creation, Redis-backed submission jobs, and a separate worker that runs Python or C++ code in a restricted Docker container.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for interactive API documentation.

To run the API, Redis, and worker together:

```bash
docker compose up --build
```

## Design decision

The API records a submission and returns `202 Accepted`; it never executes user code in the web process. A worker consumes the job from Redis and runs it inside a network-disabled, read-only container with process, CPU, memory, and wall-clock limits. The worker owns all verdict transitions: `QUEUED -> RUNNING -> final verdict`.

`docker-compose.yml` is a local-development setup. Its Docker socket mount lets the worker launch nested execution containers and must never be used on a shared production host; production workers should run on dedicated isolated nodes or a sandbox service.

The worker creates the local schema for convenience. A production deployment uses versioned database migrations and starts worker instances only after migrations complete.
