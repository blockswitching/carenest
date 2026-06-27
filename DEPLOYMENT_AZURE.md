# CareNest — Azure VM Deployment Guide

This guide walks you through deploying CareNest on an Azure Virtual Machine using Docker Compose.

---

## 1. Create an Azure VM

### Via Azure Portal

1. Go to [portal.azure.com](https://portal.azure.com) → **Create a resource** → **Virtual Machine**
2. Configure:
   - **Image:** Ubuntu 22.04 LTS
   - **Size:** Standard B2s (2 vCPU, 4 GB RAM) — minimum for production
   - **Authentication:** SSH public key (recommended)
   - **Username:** `azureuser`
   - **Inbound ports:** Allow SSH (22), HTTP (80), HTTPS (443)
3. Under **Networking**, create or select a Network Security Group (NSG) with rules:
   - SSH: port 22
   - HTTP: port 80
   - HTTPS: port 443
4. Click **Create** and wait for deployment

### Via Azure CLI (alternative)

```bash
# Login
az login

# Create resource group
az group create --name carenest-rg --location centralindia

# Create VM
az vm create \
  --resource-group carenest-rg \
  --name carenest-vm \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-sku Standard

# Open ports
az vm open-port --resource-group carenest-rg --name carenest-vm --port 80 --priority 1001
az vm open-port --resource-group carenest-rg --name carenest-vm --port 443 --priority 1002
```

### Note the public IP

```bash
az vm show --resource-group carenest-rg --name carenest-vm --show-details --query publicIps -o tsv
```

---

## 2. SSH into the VM

```bash
ssh azureuser@<YOUR_VM_PUBLIC_IP>
```

---

## 3. Install Docker & Docker Compose on the VM

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Add user to docker group (no sudo needed for docker commands)
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt install docker-compose-plugin -y

# Logout and login again for group changes to take effect
exit
```

SSH back in:
```bash
ssh azureuser@<YOUR_VM_PUBLIC_IP>

# Verify
docker --version
docker compose version
```

---

## 4. Clone Your Repository

```bash
# Using HTTPS (or set up deploy keys for SSH)
git clone https://github.com/your-org/carenest-backend.git
cd carenest-backend/carenest
```

If your repo is private, use a personal access token:
```bash
git clone https://<TOKEN>@github.com/your-org/carenest-backend.git
```

---

## 5. Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Update these values for production:

```env
# CRITICAL — change these
SECRET_KEY=generate-a-strong-random-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,<YOUR_VM_PUBLIC_IP>
DJANGO_SETTINGS_MODULE=config.settings.production

# Database
DB_NAME=carenest_db
DB_USER=postgres
DB_PASSWORD=a-strong-database-password-here
DB_HOST=db
DB_PORT=5432

# Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
REDIS_URL=redis://redis:6379/2

# CORS — your frontend URLs
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://app.your-domain.com

# Razorpay (live keys for production)
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_live_razorpay_secret

# Firebase
FIREBASE_SERVER_KEY=your_firebase_server_key

# Static/Media
STATIC_ROOT=/vol/static
MEDIA_ROOT=/vol/media

# Security
SECURE_SSL_REDIRECT=True

# Admin
ADMIN_EMAIL=admin@careforyou.in
ADMIN_PASSWORD=your-secure-admin-password

# Sentry (optional but recommended)
SENTRY_DSN=https://xxxx@sentry.io/xxxx
SENTRY_ENVIRONMENT=production
```

Generate a secure SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 6. Update docker-compose for Production

The current `docker-compose.yml` uses `config.settings.development`. For production, update the environment:

```bash
# Use sed to switch to production settings
sed -i 's/config.settings.development/config.settings.production/g' docker-compose.yml
```

Or manually edit `docker-compose.yml` and change all `DJANGO_SETTINGS_MODULE` values to `config.settings.production`.

---

## 7. Deploy with Docker Compose

```bash
# Build and start all services
docker compose up --build -d

# Check status
docker compose ps

# View logs
docker compose logs -f web
```

Expected output — all 6 services running:
```
carenest-db-1              Healthy
carenest-redis-1           Healthy
carenest-web-1             Running
carenest-celery-worker-1   Running
carenest-celery-beat-1     Running
carenest-nginx-1           Running
```

---

## 8. Verify Deployment

```bash
# Health check
curl http://localhost/api/health/

# Should return:
# {"success": true, "data": {"status": "ok", "version": "1.0.0"}, "message": ""}

# Check admin panel
curl -I http://localhost/admin/login/
# Should return HTTP 200
```

From your local machine:
```bash
curl http://<YOUR_VM_PUBLIC_IP>/api/health/
```

---

## 9. Set Up a Domain Name (Recommended)

### Point your domain to the VM

1. In your DNS provider, create an A record:
   - `api.careforyou.in` → `<YOUR_VM_PUBLIC_IP>`

2. Wait for DNS propagation (5-15 minutes)

### Add SSL with Let's Encrypt (Certbot)

```bash
# Install certbot
sudo apt install certbot -y

# Stop nginx temporarily
docker compose stop nginx

# Get certificate
sudo certbot certonly --standalone -d api.careforyou.in

# Certificates will be at:
#   /etc/letsencrypt/live/api.careforyou.in/fullchain.pem
#   /etc/letsencrypt/live/api.careforyou.in/privkey.pem
```

### Update nginx.conf for SSL

Replace `carenest/nginx.conf` with:

```nginx
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name api.careforyou.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name api.careforyou.in;
    client_max_body_size 20M;

    ssl_certificate /etc/letsencrypt/live/api.careforyou.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.careforyou.in/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location /static/ {
        alias /vol/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /vol/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

Update `docker-compose.yml` nginx service to mount certificates:

```yaml
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static_data:/vol/static:ro
      - media_data:/vol/media:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - web
```

Restart:
```bash
docker compose up -d nginx
```

### Auto-renew SSL certificates

```bash
# Create a cron job for auto-renewal
sudo crontab -e

# Add this line (renews every day at 3 AM):
0 3 * * * certbot renew --quiet --pre-hook "docker compose -f /home/azureuser/carenest-backend/carenest/docker-compose.yml stop nginx" --post-hook "docker compose -f /home/azureuser/carenest-backend/carenest/docker-compose.yml start nginx"
```

---

## 10. Set Up Automatic Updates (CI/CD)

### Option A: GitHub Actions auto-deploy

Add to `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure VM

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.AZURE_VM_IP }}
          username: azureuser
          key: ${{ secrets.AZURE_SSH_KEY }}
          script: |
            cd ~/carenest-backend/carenest
            git pull origin main
            docker compose up --build -d
            docker compose exec web python manage.py migrate --noinput
            docker compose exec web python manage.py collectstatic --noinput
```

Add these GitHub secrets:
- `AZURE_VM_IP`: Your VM public IP
- `AZURE_SSH_KEY`: Your private SSH key content

### Option B: Manual deploy

```bash
ssh azureuser@<YOUR_VM_PUBLIC_IP>
cd ~/carenest-backend/carenest
git pull origin main
docker compose up --build -d
```

---

## 11. Monitoring & Maintenance

### View logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f celery-worker
```

### Restart services

```bash
docker compose restart web
docker compose restart celery-worker
```

### Database backup

```bash
# Backup
docker compose exec db pg_dump -U postgres carenest_db > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20260627.sql | docker compose exec -T db psql -U postgres carenest_db
```

### Set up automated daily backups

```bash
mkdir -p ~/backups
crontab -e

# Add (daily at 2 AM):
0 2 * * * docker compose -f /home/azureuser/carenest-backend/carenest/docker-compose.yml exec -T db pg_dump -U postgres carenest_db > /home/azureuser/backups/carenest_$(date +\%Y\%m\%d).sql
```

### Update the app

```bash
cd ~/carenest-backend/carenest
git pull
docker compose up --build -d
```

### Check disk space

```bash
df -h
docker system df
# Clean unused images
docker system prune -f
```

---

## 12. Azure-Specific Recommendations

### Use Azure Database for PostgreSQL (optional)

For better reliability, use a managed database instead of containerized PostgreSQL:

1. Create **Azure Database for PostgreSQL - Flexible Server**
2. Update `.env`:
   ```
   DB_HOST=your-server.postgres.database.azure.com
   DB_USER=carenest_admin
   DB_PASSWORD=your-password
   DB_NAME=carenest_db
   ```
3. Remove the `db` service from `docker-compose.yml`

### Use Azure Cache for Redis (optional)

1. Create **Azure Cache for Redis** (Basic C0 is fine for starting)
2. Update `.env`:
   ```
   CELERY_BROKER_URL=rediss://:your-access-key@your-cache.redis.cache.windows.net:6380/0
   REDIS_URL=rediss://:your-access-key@your-cache.redis.cache.windows.net:6380/2
   ```
3. Remove the `redis` service from `docker-compose.yml`

### Use Azure Blob Storage for media (optional)

Instead of S3, use Azure Blob Storage:
1. Install: `pip install django-storages[azure]`
2. Update settings for `AzureStorage` backend

---

## Cost Estimate (Monthly)

| Resource | Size | Approx Cost |
|----------|------|-------------|
| VM (B2s) | 2 vCPU, 4 GB | ₹2,500/month |
| Managed PostgreSQL (Burstable B1ms) | 1 vCPU, 2 GB | ₹1,500/month |
| Azure Cache for Redis (C0) | 250 MB | ₹1,200/month |
| Domain + SSL | Let's Encrypt | Free |
| **Total (self-managed DB/Redis)** | VM only | **~₹2,500/month** |
| **Total (managed services)** | All Azure | **~₹5,200/month** |

---

## Quick Reference Commands

```bash
# SSH into VM
ssh azureuser@<IP>

# Start all services
docker compose up -d

# Stop all services
docker compose down

# Rebuild after code changes
docker compose up --build -d

# View logs
docker compose logs -f web

# Run Django management commands
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell

# Database shell
docker compose exec db psql -U postgres carenest_db
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Container keeps restarting | `docker compose logs web` — check for errors |
| CSS not loading on admin | Check nginx serves `/static/` and `collectstatic` ran |
| 502 Bad Gateway | Web container may not be ready — wait or check logs |
| Cannot connect to DB | Ensure `DB_HOST=db` in docker env, not `localhost` |
| Permission denied on /vol/ | Run `docker compose down -v` and rebuild |
| SSL cert expired | Run `sudo certbot renew` and restart nginx |
