# CodeArena deployment guide

## Local development

Use `docker compose up --build`. The stack contains the API, Redis, PostgreSQL, and a worker. The worker mounts `/var/run/docker.sock` only so it can launch local execution containers.

## Production topology

Do not reuse the development Docker-socket topology for a public multi-tenant judge. Use:

1. HTTPS reverse proxy/load balancer.
2. Multiple stateless API instances.
3. Managed PostgreSQL with backups and TLS.
4. Redis with persistence/HA appropriate to queue requirements.
5. Dedicated execution workers on isolated hosts.
6. A hardened sandbox boundary such as microVMs or a carefully configured container runtime with seccomp/AppArmor/gVisor-style isolation.
7. Secret storage rather than committed environment values.
8. Centralized logs, metrics, traces, alerts, and audit events.

## Database

The current project uses SQLAlchemy `create_all` for a simple portfolio/demo setup. Before production, introduce Alembic migrations and run migrations as a deployment step before starting API/worker replicas.

## Worker scaling

Workers are independent of API processes. Add worker replicas when queue depth increases. For a production queue, add durable acknowledgement, retries, dead-letter handling, idempotency keys, and queue-depth monitoring.

## Execution images

The judge currently supports Python 3.12 and GCC 14. Pin image digests in a security-sensitive production deployment and maintain a controlled image build pipeline instead of trusting mutable tags.

## Secrets

Generate a long random `JWT_SECRET`. Never commit `.env`, production credentials, cloud credentials, or private keys. Rotate secrets according to your deployment policy.
