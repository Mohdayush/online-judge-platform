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

## Quick start — see the project working locally

### Option A: Docker Compose (recommended)

Prerequisites: Docker Desktop with Linux containers enabled and Git.

```bash
git clone https://github.com/Mohdayush/online-judge-platform.git
cd online-judge-platform
cp .env.example .env
docker compose up --build
```

Then open:

- `http://localhost:8000` — CodeArena web application
- `http://localhost:8000/docs` — interactive Swagger/OpenAPI
- `http://localhost:8000/health` — liveness check
- `http://localhost:8000/ready` — database/Redis readiness check

Keep the terminal running while you use the application. To stop it, press `Ctrl+C`, or run `docker compose down` in another terminal.

### End-to-end demo

1. Open CodeArena and register a normal account.
2. Log in and open **Problems**.
3. Select a seeded/demo problem, or create one using the admin tooling below.
4. Choose **Python** or **C++** in the editor.
5. Submit a correct solution and watch `QUEUED → RUNNING → ACCEPTED`.
6. Submit intentionally incorrect code and verify `WRONG_ANSWER`.
7. Open **Profile** to see solved count and submission history.
8. Open **Contests**, register, and inspect the leaderboard.

To watch the asynchronous judge process a submission, open another terminal:

```bash
docker compose logs -f worker
```

You can also inspect the API logs:

```bash
docker compose logs -f api
```

### Option B: run the API locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

For real judging, Redis must be running and the worker must also be started:

```bash
python -m app.workers.submission_worker
```

## Deploy a public Live Demo for your resume

GitHub is the source-code link; a resume **Live Demo** needs a server that keeps the API, Redis, PostgreSQL, and Docker-based judge worker running.

For the current architecture, the simplest portfolio deployment is a small Linux VPS/VM with Docker installed. The repository includes `docker-compose.demo.yml` and `Caddyfile` for this single-VM deployment. Caddy provides HTTPS automatically when a DNS name points to the VM.

### 1. Provision a Linux VM

Use any VPS provider that gives you a public IPv4 address and Docker support. A small Ubuntu LTS VM is sufficient for a low-traffic personal demo. Do not put real personal/medical data or sensitive credentials into the demo.

### 2. Point a domain/subdomain to the VM

Create an A record such as:

```text
codearena.yourdomain.com  ->  YOUR_VM_PUBLIC_IP
```

If you do not own a domain, you can temporarily expose HTTP on port 80 by changing the Caddyfile to `:80`; HTTPS will not be automatic in that IP-only setup.

### 3. Install and start CodeArena

```bash
git clone https://github.com/Mohdayush/online-judge-platform.git
cd online-judge-platform
cp .env.demo.example .env.demo
nano .env.demo
```

Set:

```text
DOMAIN=codearena.yourdomain.com
PUBLIC_ORIGIN=https://codearena.yourdomain.com
JWT_SECRET=<long-random-secret>
POSTGRES_PASSWORD=<strong-random-password>
```

Then:

```bash
docker compose --env-file .env.demo -f docker-compose.demo.yml up -d --build
```

Check the services:

```bash
docker compose --env-file .env.demo -f docker-compose.demo.yml ps
docker compose --env-file .env.demo -f docker-compose.demo.yml logs -f worker
```

Open `https://codearena.yourdomain.com` in a browser. That is the URL to put beside **Live Demo** on your resume.

### 4. Create an admin and seed a demo problem

On the VM:

```bash
docker compose --env-file .env.demo -f docker-compose.demo.yml exec api python -m scripts.bootstrap_admin admin@example.com admin
```

Follow the password prompt. Use the admin account only for administration; register a separate normal account for the resume demo.

The demo seeder can create sample data when appropriate for a disposable environment. Never copy demo passwords into a public README or use them on a production system.

### 5. Resume format

Use two separate links:

```text
CodeArena — Online Judge Platform | Live Demo | GitHub
```

- **Live Demo** → your deployed HTTPS URL
- **GitHub** → `https://github.com/Mohdayush/online-judge-platform`

Do not use the GitHub repository URL as the Live Demo link: GitHub displays source code and does not run the application.

## Admin setup

Create an administrator without placing the password in shell history:

```bash
python -m scripts.bootstrap_admin admin@example.com adminuser
```

The script prompts for the password. For a disposable local database, the demo seeder can create sample data; do not expose demo credentials on a public deployment.

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

**Important:** the local/demo worker mounts the host Docker socket so it can create execution containers. A Docker socket is highly privileged and must not be exposed to an untrusted workload. The demo Compose topology is suitable for a low-traffic portfolio demonstration on a dedicated VM, not a shared hostile multi-tenant judge. See [`docs/SECURITY.md`](docs/SECURITY.md) and [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

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
docker-compose.demo.yml single-VM live-demo stack
Caddyfile              HTTPS reverse proxy
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

CodeArena is designed as an interview/portfolio-quality reference implementation rather than a claim that arbitrary code is safely isolated for a hostile public multi-tenant service. A real public judge should add versioned Alembic migrations, durable queue acknowledgements/retries/dead-letter handling, stronger VM or microVM isolation, pinned execution-image digests, per-test resource accounting, rate limiting, audit logs, observability, secret management, and a dedicated execution cluster. The deployment guide documents that topology.

## License

MIT — see [`LICENSE`](LICENSE).
