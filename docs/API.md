# CodeArena API reference

Base URL: `/api/v1`

FastAPI also exposes interactive OpenAPI documentation at `/docs`.

## Authentication

### Register
`POST /auth/register`

```json
{"email":"user@example.com","username":"user123","password":"strong-password"}
```

### Login
`POST /auth/login`

Returns a bearer JWT. Send it as `Authorization: Bearer <token>`.

## Users

- `GET /users/me` — current user
- `GET /users/me/stats` — submission, acceptance, and solved counts
- `GET /users/me/submissions?limit=20` — recent submissions

## Problems

- `GET /problems` — public problem list; optional `difficulty=EASY|MEDIUM|HARD`
- `GET /problems/{slug}` — public problem details
- `POST /problems` — admin only
- `PUT /problems/{id}` — admin only
- `DELETE /problems/{id}` — admin only; protected when referenced
- `POST /problems/{id}/test-cases` — admin only
- `GET /problems/{id}/test-cases` — admin only; hidden data is never exposed publicly
- `DELETE /test-cases/{id}` — admin only

## Submissions

`POST /submissions` accepts `python` or `cpp` and returns `202` with status `QUEUED`.

The API never executes contestant source. A Redis job is consumed by the worker, which executes each test case inside Docker.

Poll `GET /submissions/{id}` until the status is final:

- `ACCEPTED`
- `WRONG_ANSWER`
- `COMPILATION_ERROR`
- `RUNTIME_ERROR`
- `TIME_LIMIT_EXCEEDED`
- `MEMORY_LIMIT_EXCEEDED`
- `SYSTEM_ERROR`

## Contests

- `GET /contests`
- `GET /contests/{id}`
- `GET /contests/{id}/problems`
- `POST /contests` — admin only
- `POST /contests/{id}/register` — authenticated user
- `GET /contests/{id}/leaderboard`
- Contest submissions require registration, a mapped problem, and an active contest window.

## Security notes

Public problem responses contain no test-case input/output and submission responses contain no source code. Administrative endpoints require an authenticated user whose current database role is `ADMIN`.
