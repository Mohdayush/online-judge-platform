# CodeArena Completion

This file marks the project-completion milestone and documents the intended production boundary.

## Implemented architecture

- FastAPI REST API
- JWT authentication with Argon2 password hashing
- Role-based admin APIs
- SQLAlchemy persistence
- Redis-backed asynchronous submission queue
- Separate submission worker
- Docker-isolated Python/C++ execution
- Resource and network restrictions in the sandbox
- Submission verdict lifecycle
- Contest registration and leaderboard
- Browser frontend served by FastAPI
- Docker Compose development environment
- Automated test suite and CI-ready project structure

## Security boundary

Contestant source code must never execute inside the API process. The development worker talks to Docker through the host Docker socket only for local execution. A production deployment should place workers on dedicated sandbox hosts and use a stronger container/VM isolation boundary.

## Supported languages

- Python 3.12
- C++ (GCC 14)

## Verdicts

QUEUED, RUNNING, ACCEPTED, WRONG_ANSWER, COMPILATION_ERROR, RUNTIME_ERROR, TIME_LIMIT_EXCEEDED, MEMORY_LIMIT_EXCEEDED, SYSTEM_ERROR.
