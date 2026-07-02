# CI/CD Pipeline

Workflow file: `.github/workflows/deploy.yml`

## What It Does

1. **On every push to `main`:**
   - Checks out the code
   - Builds the FastAPI Docker image (validates the Dockerfile actually builds)
   - Pushes the image to GitHub Container Registry (GHCR)
   - Runs the deploy job

2. **Deploy job:**
   - Runs `docker compose up -d --build` to bring the stack up/refresh it
   - Prunes old dangling images
   - Curls `/health` to confirm the deploy actually worked, fails the job if not

## Why "self-hosted" Runner (Important Local-Deployment Note)

GitHub's hosted runners (`ubuntu-latest`) run in GitHub's cloud and have no
network path to a machine sitting behind your home router or on localhost.
To make the pipeline **actually deploy somewhere real** without a public VPS,
this workflow uses `runs-on: self-hosted`.

### Setting Up a Self-Hosted Runner (works on your own PC or a VPS)

1. Go to your GitHub repo → Settings → Actions → Runners → New self-hosted runner.
2. Follow GitHub's generated commands to download and configure the runner
   on the target machine (your PC or a server), e.g.:
   ```bash
   ./config.sh --url https://github.com/<you>/<repo> --token <token>
   ./run.sh
   ```
3. Now pushes to `main` will trigger the workflow, and the `deploy` job will
   execute directly on that machine — a real, working CI/CD deploy, just
   targeting your own machine instead of a rented VPS.

## Alternate Path: Deploying to a Real Remote VPS via SSH

If you do have a VPS, the workflow file has a commented-out `deploy-remote`
job using `appleboy/ssh-action`. To use it:

1. Generate an SSH key pair, add the public key to the VPS's
   `~/.ssh/authorized_keys`.
2. Add these secrets in GitHub repo → Settings → Secrets → Actions:
   - `SERVER_HOST` — VPS IP
   - `SERVER_USER` — SSH username
   - `SSH_PRIVATE_KEY` — the private key
3. Uncomment the `deploy-remote` job, comment out/remove the self-hosted one.
4. Push to `main` — GitHub Actions will SSH in and redeploy automatically.

## Zero-Downtime Note

The current `docker compose up -d --build` causes a brief restart gap for
the `app` service. For true zero-downtime:
- Run 2+ replicas of the `app` service behind NGINX and roll them one at a
  time, or
- Use a tool like Docker Swarm / Kubernetes for rolling updates, or
- Use `docker compose up -d --build --no-deps app` combined with NGINX
  health-check-based upstream removal.

This is called out as a bonus-tier improvement, not implemented in the base
setup, to keep the stack simple.
