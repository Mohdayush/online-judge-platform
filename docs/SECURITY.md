# CodeArena Security Notes

## Trust boundaries

1. Browser clients are untrusted.
2. The FastAPI API validates requests and never executes contestant source.
3. Redis transports submission IDs, not executable code.
4. The worker is a privileged service and therefore must not be exposed to untrusted users.
5. Contestant programs execute inside a separate Docker container in development.

## Sandbox controls

The development sandbox uses no network, a read-only root filesystem, a temporary writable filesystem, process limits, CPU limits, memory limits, and a wall-clock timeout. Source is mounted read-only.

## Authentication

Passwords are hashed with Argon2 through `pwdlib`. API access uses signed JWT bearer tokens. Admin-only operations are protected by a role dependency.

## Data exposure

Hidden test cases have no public read endpoint. Submission source is returned only to its owner or an administrator.

## Production checklist

- Replace the development JWT secret with a randomly generated secret stored in a secret manager.
- Use HTTPS and secure reverse-proxy headers.
- Use PostgreSQL and versioned migrations.
- Add API rate limiting and request-size limits at the edge.
- Move execution to dedicated sandbox hosts or hardened VMs.
- Add seccomp/AppArmor/gVisor or VM-level isolation.
- Never mount the host Docker socket into a publicly reachable worker.
- Restrict worker credentials and network egress.
- Add audit logs, metrics, tracing, alerting, and retention policies.
- Scan dependencies and container images in CI.
