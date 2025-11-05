# Production Deployment

This directory contains the production deployment configuration for the Florence Trees application using Docker Compose and Caddy as a reverse proxy.

## Architecture

- **Caddy**: Reverse proxy with automatic HTTPS/SSL certificates via Let's Encrypt
- **Backend**: FastAPI application serving the REST API
- **Database**: PostgreSQL for persistent data storage
- **Frontend**: Vue.js static build served directly by Caddy

## Prerequisites

- Docker and Docker Compose installed on your VPS
- Domain name (florence-trees.fralo.dev) pointing to your VPS IP address
- Ports 80 and 443 open on your firewall

## Deployment Steps

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd test-deepforest/devops/production
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your secrets:

```bash
cp .env.example .env
nano .env
```

Update the following values in `.env`:
- `POSTGRES_USER`: Your PostgreSQL username
- `POSTGRES_PASSWORD`: A strong, secure password for PostgreSQL
- `DATABASE_URL`: Update with your PostgreSQL credentials
- `CADDY_EMAIL`: Your email for Let's Encrypt SSL certificates (also update in Caddyfile)

Copy and update the email in `Caddyfile` line 3 to match your actual email address.

### 3. Build the Frontend

The frontend needs to be built before starting the services:

```bash
./build-frontend.sh
```

This will:
- Build the Vue.js frontend with production optimizations
- Extract the static files to `./frontend_dist`
- These files will be served directly by Caddy

### 4. Start the Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Backend API server
- Caddy reverse proxy with automatic SSL

### 5. Verify Deployment

Check that all services are running:

```bash
docker-compose ps
```

Check logs:

```bash
docker-compose logs -f
```

Visit your site:
- Frontend: https://florence-trees.fralo.dev
- API: https://florence-trees.fralo.dev/api/
- API Docs: https://florence-trees.fralo.dev/docs

## SSL Certificates

Caddy automatically handles SSL certificate provisioning and renewal via Let's Encrypt. Certificates are stored in the `caddy_data` volume and will be automatically renewed before expiration.

## Updating the Application

### Update Backend

```bash
git pull
docker-compose build backend
docker-compose up -d backend
```

### Update Frontend

```bash
git pull
./build-frontend.sh
docker-compose restart caddy
```

## Data Backup

### Backup Database

```bash
docker-compose exec db pg_dump -U <POSTGRES_USER> <POSTGRES_DB> > backup.sql
```

### Restore Database

```bash
docker-compose exec -T db psql -U <POSTGRES_USER> <POSTGRES_DB> < backup.sql
```

## Monitoring

View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f caddy
docker-compose logs -f db
```

## Troubleshooting

### SSL Certificate Issues

If SSL certificates fail to provision:
1. Ensure your domain DNS is correctly pointing to your VPS
2. Check ports 80 and 443 are accessible
3. Verify email in Caddyfile is valid
4. Check Caddy logs: `docker-compose logs caddy`

### Database Connection Issues

1. Check database is healthy: `docker-compose ps`
2. Verify DATABASE_URL in .env matches POSTGRES credentials
3. Check backend logs: `docker-compose logs backend`

### Frontend Not Loading

1. Ensure `frontend_dist` directory exists and contains files
2. Re-run `./build-frontend.sh`
3. Restart Caddy: `docker-compose restart caddy`

## Security Notes

- Never commit the `.env` file to version control (it's in .gitignore)
- Use strong passwords for database credentials
- Regularly update Docker images: `docker-compose pull && docker-compose up -d`
- Monitor access logs in Caddy data volume
- Consider setting up automated backups

## Maintenance

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Data (⚠️ DESTRUCTIVE)

```bash
docker-compose down -v
```

### Update Docker Images

```bash
docker-compose pull
docker-compose up -d
```
