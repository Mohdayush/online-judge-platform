# CodeArena — Online Judge Platform

CodeArena is a portfolio-grade asynchronous online judge that demonstrates backend engineering, relational data modeling, authentication, queues, worker architecture, secure code execution boundaries, contests, and a browser client.

## What is included

- FastAPI REST API with OpenAPI/Swagger
- JWT authentication and Argon2 password hashing
- User/admin role-based access control
- User profile, statistics, solved-problem counts, and submission history
- Problem CRUD for administrators
- Public problem browsing with difficulty filtering
- Hidden test-case management with public-data protection
- Python 3.12 and C++/GCC 14 judging
- Redis-backed asynchronous submission queue
- Dedicated submission worker
- Docker execution sandbox with network isolation, read-only root filesystem, dropped Linux capabilities, no-new-privileges, CPU/memory/process/file limits, temporary filesystems, and wall-clock timeout
- Verdicts: `QUEUED`, `RUNNING`, `ACCEPTED`, `WRONG_ANSWER`, `COMPILATION_ERROR`, `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`, `MEMORY_LIMIT_EXCEEDED`, `SYSTEM_ERROR`
- Contest creation, registration, contest problem sets, contest submissions, and leaderboards
- Browser UI for authentication, problem search, code submission, verdict polling, profile/statistics, submission history, contests, registration, and leaderboards
- Docker Compose development stack with API, PostgreSQL, Redis, and worker
- CI for tests, Python compilation, frontend syntax, whitespace, and Docker image builds
- Admin bootstrap and demo seed scripts
- Architecture, security, API, and deployment documentation

## Architecture

```text
                           Browser
                              |
                              v
                       +--------------+
                       |   FastAPI    |
                       | REST + Auth  |
                       +------+-------+
                              |
                 +------------+-------------+
                 |                          |
                 v                          v
          +-------------+             +-----------+
          | PostgreSQL  |             |   Redis   |
          +-------------+             |   Queue   |
                                      +-----+-----+
                                            |
                                            v
                                     +-------------+
                                     | Judge Worker|
                                     +------+------+ 
                                            |
                                            v
                                     +-------------+
                                     | Docker      |
                                     | Sandbox     |
                                     +------+------+ 
                                            |
                                      +-----+-----+
                                      |           |
                                    Python       C++
```

The API accepts a submission and returns `202 Accepted`. It never executes contestant code in the web process. The worker consumes the submission ID, loads the problem's test cases, runs the source inside the sandbox, compares output, and persists the final verdict.

## Quick start

### Docker Compose

```bash
git clone https://github.com/Mohdayush/online-judge-platform.git
cd online-judge-platform
cp .env.example .env
docker compose up --build
```

Open `http://localhost:8000` for CodeArena and `http://localhost:8000/docs` for Swagger/OpenAPI.

### Local API

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

For real judging, run Redis and then:

```bash
python -m app.workers.submission_worker
```

## Admin setup

Create an administrator without placing the password in shell history:

```bash
python -m scripts.bootstrap_admin admin@example.com adminuser
```

The script prompts for the password. For a disposable local database, the demo seeder can create a sample problem and administrator; do not expose demo credentials on a public deployment.

## API workflow

1. Register or log in.
2. Browse `GET /api/v1/problems`.
3. Submit code with `POST /api/v1/submissions`.
4. The API stores the submission as `QUEUED` and publishes its ID to Redis.
5. A worker changes it to `RUNNING` and executes all configured test cases.
6. The worker records the final verdict.
7. Poll `GET /api/v1/submissions/{id}` or view `GET /api/v1/users/me/submissions`.

Full endpoint details are in [`docs/API.md`](docs/API.md).

## Security boundary

The execution layer is intentionally separated from the API. Development execution uses Docker with no network, a read-only root filesystem, a writable temporary workspace, dropped capabilities, `no-new-privileges`, CPU/memory/process limits, file-size limits, and a wall-clock timeout. Contestant source is mounted read-only.

**Important:** the local worker mounts the host Docker socket so it can create execution containers. A Docker socket is highly privileged and must not be exposed to an untrusted workload. The Compose file is a development/demo topology, not a shared public production sandbox. See [`docs/SECURITY.md`](docs/SECURITY.md) and [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Project structure

```text
app/
  api/                 REST endpoints
  core/                settings and database
  models/              SQLAlchemy entities
  schemas/             Pydantic request/response contracts
  services/            auth, Redis queue, Docker sandbox
  workers/             asynchronous judge worker
web/                   browser client
scripts/               admin and demo helpers
tests/                 automated tests
docs/                  architecture, API, security, deployment
.github/workflows/     CI
Dockerfile             API image
Dockerfile.worker      worker image
docker-compose.yml     local stack
```

## Testing

```bash
pytest -q
python -m compileall -q app scripts
node --check web/app.js
git diff --check
docker build -t codearena-api .
docker build -t codearena-worker -f Dockerfile.worker .
```

GitHub Actions runs the automated checks on pushes and pull requests targeting `main`.

## Production boundary

CodeArena is designed to be an interview/portfolio-quality reference implementation rather than a claim that arbitrary code is safely isolated for a hostile public multi-tenant service. A real public judge should add versioned Alembic migrations, durable queue acknowledgements/retries/dead-letter handling, stronger VM or microVM isolation, pinned execution-image digests, per-test resource accounting, rate limiting, audit logs, observability, secret management, and a dedicated execution cluster. The deployment guide documents that topology.

## License

MIT — see [`LICENSE`](LICENSE).
