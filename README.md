# CodeArena — Online Judge Platform

CodeArena is a portfolio-grade, asynchronous online judge inspired by the core workflow of platforms such as LeetCode and HackerRank. It demonstrates API design, authentication, relational data modeling, Redis queues, background workers, containerized execution, contest scoring, and a browser client.

## Architecture

```text
Browser
   |
   v
FastAPI API ----> SQLAlchemy DB
   |
   +-----------> Redis submission queue
                    |
                    v
              Submission Worker
                    |
                    v
             Docker Sandbox
              /           \
          Python          C++
```

The API creates a submission and immediately returns `202 Accepted`. It never executes contestant code in the web process. A separate worker consumes submission IDs, loads the problem's test cases, runs the source inside a restricted Docker container, compares output, and persists the final verdict.

## Features

- JWT authentication with Argon2 password hashing
- User and admin roles
- Problem creation and test-case management
- Hidden test cases are never returned by the public problem API
- Python 3.12 and C++ (GCC 14) execution
- Redis-backed asynchronous submission queue
- Submission polling and submission history
- Verdicts: `QUEUED`, `RUNNING`, `ACCEPTED`, `WRONG_ANSWER`, `COMPILATION_ERROR`, `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`, `MEMORY_LIMIT_EXCEEDED`, `SYSTEM_ERROR`
- Contest creation, registration, contest submissions, and leaderboard scoring
- Browser UI for authentication, problems, submissions, contests, and leaderboards
- Docker Compose development environment
- GitHub Actions CI
- Environment template, license, seed/admin tooling, and architecture documentation

## Quick start

### Option A: Docker Compose

```bash
git clone https://github.com/Mohdayush/online-judge-platform.git
cd online-judge-platform
cp .env.example .env
docker compose up --build
```

Open `http://localhost:8000` for the web client and `http://localhost:8000/docs` for Swagger/OpenAPI.

### Option B: API locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run Redis separately if you want real submission processing. The worker can then be started with:

```bash
python -m app.workers.submission_worker
```

## Demo data and admin

The project contains helper scripts under `scripts/` for bootstrapping an administrator and loading demonstration problems. Use them only in a local/dev database and supply your own credentials through environment variables where supported.

## API flow

1. Register or log in to obtain a bearer token.
2. Browse problems with `GET /api/v1/problems`.
3. Submit source code with `POST /api/v1/submissions`.
4. The API stores the submission as `QUEUED` and pushes its ID to Redis.
5. The worker changes it to `RUNNING` and executes every configured test case.
6. The worker records `ACCEPTED`, `WRONG_ANSWER`, `COMPILATION_ERROR`, `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`, or `SYSTEM_ERROR`.
7. Poll `GET /api/v1/submissions/{id}` or inspect submission history.

## Security boundary

The execution layer is intentionally separated from the API. Development execution uses Docker with `--network none`, a read-only root filesystem, a writable temporary filesystem, CPU/memory/process limits, and a wall-clock timeout. Source files are mounted read-only.

This is a learning/portfolio implementation, not a claim of production-grade arbitrary-code isolation. The Docker socket mounted by the local Compose worker is highly privileged. **Never expose that socket to untrusted workloads or use this Compose topology as a shared production sandbox.** Production should use dedicated sandbox hosts or a hardened VM/container execution service with additional syscall, filesystem, network, and identity isolation.

## Project structure

```text
app/
  api/                 REST endpoints
  core/                configuration and database
  models/              SQLAlchemy entities
  schemas/             Pydantic contracts
  services/            authentication, queue, sandbox
  workers/             asynchronous judge worker
web/                   browser client
scripts/               local bootstrap/seed helpers
tests/                 automated tests
.github/workflows/     CI
Dockerfile             API image
Dockerfile.worker      worker image
docker-compose.yml     local API + Redis + worker stack
```

## Testing

```bash
pytest -q
python -m compileall -q app scripts
node --check web/app.js
git diff --check
```

## Important production upgrades

Before deploying a public judge, add versioned Alembic migrations, PostgreSQL, durable queue semantics/dead-letter handling, stronger sandboxing (seccomp/AppArmor/gVisor/VM isolation), per-test resource accounting, rate limiting, audit logging, object storage for large artifacts, observability, secret management, and a dedicated execution cluster.

## License

MIT. See `LICENSE`.
