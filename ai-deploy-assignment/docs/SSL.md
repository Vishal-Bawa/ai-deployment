# SSL Setup

This project documents two SSL paths since it was primarily built and tested
**locally without a public domain**.

## Option A — Self-Signed Certificate (Local / No Domain)

Use this for local development/testing, or if your assignment evaluator just
wants to see HTTPS is configured correctly even without real public trust.

1. Generate a self-signed cert:
   ```bash
   mkdir -p certs
   openssl req -x509 -nodes -days 365 \
     -newkey rsa:2048 \
     -keyout certs/privkey.pem \
     -out certs/fullchain.pem \
     -subj "/CN=localhost"
   ```

2. Uncomment the HTTPS `server` block in `nginx/nginx.conf`.

3. Restart NGINX:
   ```bash
   docker compose restart nginx
   ```

4. Test:
   ```bash
   curl -k https://localhost/health
   ```
   (`-k` skips certificate validation since it's self-signed — browsers will
   show a warning too, which is expected and fine for local testing.)

## Option B — Let's Encrypt (Real VPS + Domain)

Use this once you have an actual VPS with a public IP and a domain (or free
subdomain from something like DuckDNS or Cloudflare) pointed at it.

1. Point your domain's DNS A record at the VPS's public IP.

2. Install certbot on the VPS:
   ```bash
   sudo apt-get install certbot
   ```

3. Temporarily stop NGINX container (or run certbot in standalone mode on a
   free port), then issue the cert:
   ```bash
   sudo certbot certonly --standalone -d yourdomain.com
   ```

4. Copy the generated certs into this project's `certs/` folder:
   ```bash
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./certs/
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./certs/
   ```

5. Uncomment the HTTPS server block in `nginx/nginx.conf`, set
   `server_name yourdomain.com;`, and restart:
   ```bash
   docker compose restart nginx
   ```

6. Set up auto-renewal (Let's Encrypt certs expire every 90 days):
   ```bash
   sudo crontab -e
   # add:
   0 3 * * * certbot renew --quiet && docker compose restart nginx
   ```

## Why This Project Doesn't Ship With SSL "On" by Default

Since it targets both localhost and a real VPS, SSL is left as an opt-in
step (uncomment a config block) rather than forced on — a self-signed cert
on `localhost` provides no real security benefit for local dev, and a real
cert requires a domain the evaluator running this locally won't have.
