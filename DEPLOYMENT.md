# Deployment Guide - Docker Compose

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)
- At least 2GB RAM available

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Puisaeroyi/test-leave.git
   cd test-leave
   ```

2. **Configure environment**
   ```bash
   # Copy the example environment file
   cp .env.docker.example .env.docker

   # Edit if needed (optional for development)
   # nano .env.docker
   ```

3. **Start all services**
   ```bash
   docker-compose up -d --build
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000/api/v1
   - Admin Panel: http://localhost:8000/admin

## Services

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| PostgreSQL | `leave_db` | 5432 | Database |
| Backend | `leave_backend` | 8000 | Django API |
| Frontend | `leave_frontend` | 5173 | Vite dev server |

## Docker Commands

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f db
```

### Rebuild after code changes
```bash
docker-compose up -d --build
```

### Run Django management commands
```bash
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py seed_data
```

### Restart a service
```bash
docker-compose restart backend
```

## Database Management

### PostgreSQL Connection
```
Host: localhost
Port: 5432
Database: leave_management
User: postgres
Password: postgres
```

### Access PostgreSQL directly
```bash
docker-compose exec db psql -U postgres -d leave_management
```

### Backup database
```bash
docker-compose exec db pg_dump -U postgres leave_management > backup.sql
```

### Restore database
```bash
cat backup.sql | docker-compose exec -T db psql -U postgres -d leave_management
```

## Troubleshooting

### Port already in use
Edit `docker-compose.yml` to change ports:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

### Database connection errors
```bash
# Check database health
docker-compose ps

# Restart database
docker-compose restart db

# View database logs
docker-compose logs db
```

### Clear everything and restart
```bash
docker-compose down -v  # Removes volumes too
docker-compose up -d --build
```

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Run migrations manually
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

## Production Deployment

For production, update these settings:

1. **`.env.docker`**
   ```bash
   DJANGO_SECRET_KEY=<generate-secure-key>
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=yourdomain.com
   ```

2. **`docker-compose.yml`** - Update database passwords:
   ```yaml
   environment:
     POSTGRES_PASSWORD: <secure-password>
   ```

3. **Generate secure secret key**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

## File Structure

```
.
├── docker-compose.yml      # Main Docker Compose configuration
├── Dockerfile.backend      # Backend container definition
├── frontend/
│   └── Dockerfile          # Frontend container definition
├── .env.docker.example     # Environment template
├── .env.docker            # Your environment (create from example)
└── requirements.txt        # Python dependencies
```

## Default Credentials

After running `seed_data`:
- Admin user: Check seed data or create superuser manually
- Default organizations: Created by seed script

## Notes

- PostgreSQL data persists in Docker volume `postgres_data`
- Media files are stored in `./media` directory
- Backend runs with 4 workers (adjust in `docker-compose.yml` if needed)
- Frontend runs in dev mode with hot reload
