# Deployment Documentation

## Architecture

```
                    ┌─────────────┐
   Internet/User ──▶│   NGINX     │  (ports 80/443, reverse proxy)
                    └──────┬──────┘
                           │ internal docker network "backend"
                           ▼
                    ┌─────────────┐
                    │  FastAPI    │  (port 8000, not exposed to host)
                    │  (app)      │
                    └──┬───────┬──┘
                       │       │
              ┌────────▼─┐   ┌▼─────────┐
              │ Postgres │   │  Redis   │
              │ (data)   │   │ (cache)  │
              └──────────┘   └──────────┘
```

Only NGINX is exposed to the host machine / internet. FastAPI, Postgres, and
Redis all sit on an internal Docker network (`backend`) and are unreachable
from outside — this is a basic but important security boundary.

## Prerequisites

- Docker Engine 24+ and Docker Compose v2 (`docker compose version`)
- Git

## Local Setup (Step by Step)

1. **Clone the repo**
   ```bash
   git clone <your-repo-url>
   cd ai-deploy-assignment
   ```

2. **Create your environment file**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set real values for `POSTGRES_PASSWORD` and `REDIS_PASSWORD`.
   Never commit this file — it's already in `.gitignore`.

3. **Build and start the stack**
   ```bash
   docker compose up -d --build
   ```

4. **Check everything is healthy**
   ```bash
   docker compose ps
   ```
   All services should show `healthy` or `running`.

5. **Test the health endpoint**
   ```bash
   curl http://localhost/health
   ```
   Expected response:
   ```json
   {"status": "ok", "checks": {"postgres": "ok", "redis": "ok"}}
   ```

6. **Test the API**
   ```bash
   curl -X POST http://localhost/items -H "Content-Type: application/json" -d '{"name":"test item"}'
   curl http://localhost/items/1
   ```

7. **View logs**
   ```bash
   docker compose logs -f app
   ```

8. **Stop everything**
   ```bash
   docker compose down
   ```
   (Add `-v` to also wipe database/redis volumes — use with caution.)

## Deploying to a VPS (Production Path)

If deploying to a real server instead of localhost:

1. Provision a VPS (DigitalOcean, Hetzner, Oracle Cloud Free Tier, etc.) running Ubuntu 22.04/24.04.
2. Run `scripts/server_hardening.sh` on the fresh server (sets up firewall, fail2ban, disables password SSH login, installs Docker).
3. Clone the repo onto the server, e.g. into `/opt/ai-deploy-assignment`.
4. Set up `.env` on the server (same as local step 2).
5. Point your domain's DNS A record at the server's IP (if you have a domain).
6. Follow `docs/SSL.md` to get a real Let's Encrypt certificate, or use the
   self-signed cert approach if no domain is available.
7. Run `docker compose up -d --build`.
8. Configure CI/CD (see `docs/CICD.md`) so future `git push` deploys automatically.

## Environment Variables

| Variable | Description | Where used |
|---|---|---|
| `POSTGRES_DB` | Database name | postgres, app |
| `POSTGRES_USER` | Database user | postgres, app |
| `POSTGRES_PASSWORD` | Database password | postgres, app |
| `POSTGRES_HOST` | DB hostname (docker service name) | app |
| `POSTGRES_PORT` | DB port | app |
| `REDIS_HOST` | Redis hostname (docker service name) | app |
| `REDIS_PORT` | Redis port | app |
| `REDIS_PASSWORD` | Redis auth password | redis, app |
| `ENVIRONMENT` | dev/staging/production flag | app (optional use) |

## Logging Strategy

- All containers log to stdout/stderr (12-factor app style), captured by Docker's
  `json-file` driver with rotation (`max-size: 10m`, `max-file: 3`) to prevent
  disk from filling up.
- Application logs use Python's `logging` module with timestamps and log levels.
- To view live logs: `docker compose logs -f <service>`
- To view all logs since a time: `docker compose logs --since 1h`
- **Production improvement (not implemented here, noted for completeness):**
  ship logs to a centralized system like Loki, ELK, or a hosted service
  (e.g. Better Stack, Datadog) rather than relying on local `json-file` logs.

## Backup & Restart Strategy

- **Backups:** `scripts/backup.sh` dumps Postgres to a timestamped, gzip-compressed
  `.sql.gz` file in `./backups/`, and prunes backups older than 7 days.
  Schedule it with cron on the server:
  ```
  0 2 * * * /opt/ai-deploy-assignment/scripts/backup.sh >> /var/log/db_backup.log 2>&1
  ```
- **Restore:** `scripts/restore.sh <backup-file>` restores a given backup into
  the running Postgres container.
- **Restart policy:** all services use `restart: unless-stopped` in
  `docker-compose.yml`, so they automatically come back up after a crash or
  server reboot (unless manually stopped).
- **Zero-downtime consideration:** the current setup has a brief restart gap
  on redeploy. See `docs/CICD.md` for a note on rolling deploys.

## Security Measures Implemented

- Non-root user inside the FastAPI container
- Postgres and Redis are not exposed to the host/internet — only reachable
  from other containers on the internal `backend` network
- Redis requires a password (`--requirepass`)
- NGINX hides its version banner (`server_tokens off`)
- Basic rate limiting on the API via NGINX (`limit_req_zone`)
- Secrets loaded from `.env`, never hardcoded, `.env` excluded from git
- `scripts/server_hardening.sh` sets up `ufw` firewall, `fail2ban`, and
  disables SSH password login for a real VPS deployment

## Known Limitations / Honest Notes

- This was built and tested locally with Docker Desktop / Docker Engine.
  No public domain was available, so SSL is documented with both a
  self-signed-cert path (works anywhere) and a Let's Encrypt path (for
  when a real domain + VPS is used) — see `docs/SSL.md`.
- The CI/CD pipeline is written to work with a self-hosted GitHub Actions
  runner (so it can reach a local machine or private server) with a
  commented-out alternate job for SSH-based deployment to a public VPS.
