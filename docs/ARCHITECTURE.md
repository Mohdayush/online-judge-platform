# CodeArena Architecture

## Request path

```text
Client -> FastAPI -> validate/authenticate -> DB transaction -> Redis queue -> 202 response
```

The API stores the submission before enqueueing its ID. This keeps request latency independent from compilation/execution time.

## Worker path

```text
Redis -> worker -> load submission/problem/tests -> RUNNING
      -> execute each test in Docker -> compare output
      -> final verdict -> DB
```

A submission stops at the first failing test. Accepted submissions have passed every configured test case.

## Contest path

Users register for a contest. During the active contest window, submissions may reference the contest only when the user is registered and the problem belongs to that contest. The leaderboard awards each user the points for the first accepted submission of each contest problem and orders results by score, solved count, penalty time, then username.

## Persistence

SQLAlchemy models represent users, problems, test cases, submissions, contests, contest problems, registrations, and contest submissions. SQLite is convenient for local development; PostgreSQL is recommended for deployment.

## Scaling

API instances can scale horizontally because execution is moved to workers. Redis provides the asynchronous boundary. Worker instances can be scaled independently based on queue depth. A production implementation should use durable queue semantics, retries/dead-letter handling, and idempotent job processing.

## Production boundary

The included Docker Compose topology is for local development. The worker's Docker socket mount is intentionally documented as a privileged development mechanism. A public judge needs a stronger isolation service and dedicated execution infrastructure.
