# AI Deploy Assignment

A dockerized FastAPI + PostgreSQL + Redis + NGINX stack, with CI/CD via
GitHub Actions, health checks, logging, backups, and documented SSL/security
setup for both **local** and **VPS** deployment.

## Quick Start (Local)

```bash
git clone <your-repo-url>
cd ai-deploy-assignment
cp .env.example .env        # edit passwords inside
docker compose up -d --build
curl http://localhost/health
```

## Project Structure

```
.
├── app/                      # FastAPI application
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── nginx/
│   └── nginx.conf            # reverse proxy + SSL config (HTTP + commented HTTPS)
├── scripts/
│   ├── backup.sh             # Postgres backup with rotation
│   ├── restore.sh            # Restore from a backup file
│   └── server_hardening.sh   # ufw + fail2ban + SSH hardening for a VPS
├── docs/
│   ├── DEPLOYMENT.md         # full deployment walkthrough + architecture
│   ├── SSL.md                # self-signed (local) vs Let's Encrypt (VPS) SSL
│   └── CICD.md                # CI/CD pipeline explanation, self-hosted runner setup
├── .github/workflows/
│   └── deploy.yml             # build + deploy pipeline
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Read Next

- Full deployment steps → [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- SSL setup (local + VPS) → [`docs/SSL.md`](docs/SSL.md)
- CI/CD pipeline details → [`docs/CICD.md`](docs/CICD.md)

## Health Check

```
GET /health
→ {"status": "ok", "checks": {"postgres": "ok", "redis": "ok"}}
```

## Tech Stack

- **FastAPI** — API framework
- **PostgreSQL 16** — persistent data store
- **Redis 7** — caching layer (cache-aside pattern on `/items/{id}`)
- **NGINX** — reverse proxy, rate limiting, TLS termination
- **Docker Compose** — orchestration
- **GitHub Actions** — CI/CD
