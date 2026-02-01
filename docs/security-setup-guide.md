# Security Setup Quick Reference

## Environment Variables Setup

### Local Development (Virtualenv)

Create `.env` file in project root:

```bash
# Django Core
DJANGO_SECRET_KEY=your-local-dev-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/leave_management

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Docker Development

Uses `.env.docker` (already created):

```bash
DJANGO_SECRET_KEY=dev-only-docker-secret-key-change-in-production-please
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,backend,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Production

Create `.env.production`:

```bash
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_SECRET_KEY=<generated-secret-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com,api.your-domain.com
DATABASE_URL=postgresql://user:password@host:5432/dbname
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

## Quick Commands

### Generate SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Run Django Security Check

```bash
# Set environment variables first
export DJANGO_SECRET_KEY="test-key"
export DJANGO_DEBUG="False"
export DJANGO_ALLOWED_HOSTS="example.com"

# Run check
python manage.py check --deploy
```

### Test Docker Configuration

```bash
# Rebuild and start
docker-compose down
docker-compose up --build

# Check environment variables in container
docker-compose exec backend env | grep DJANGO

# Test health check (if implemented)
docker-compose exec backend curl http://localhost:8000/healthz/
```

### Verify Security Headers

```bash
# Check headers (production)
curl -I https://your-domain.com

# Should include:
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Referrer-Policy: strict-origin-when-cross-origin
```

## Troubleshooting

### "DJANGO_SECRET_KEY must be set in production"

**Solution:** Set the environment variable or set DJANGO_DEBUG=True for development

### "DJANGO_ALLOWED_HOSTS must be set in production"

**Solution:** Set DJANGO_ALLOWED_HOSTS with your domain names

### "Invalid DJANGO_DEBUG value"

**Solution:** Use True, False, 1, or 0 (case-insensitive)

### CORS errors in browser

**Solution:** Add your frontend URL to CORS_ALLOWED_ORIGINS or set DJANGO_DEBUG=True

### CSRF token failures

**Solution:** Check CSRF_TRUSTED_ORIGINS is auto-generated from ALLOWED_HOSTS

## Security Checklist

Before deploying to production:

- [ ] Generate unique SECRET_KEY
- [ ] Set DJANGO_DEBUG=False
- [ ] Configure DJANGO_ALLOWED_HOSTS (no wildcards)
- [ ] Set CORS_ALLOWED_ORIGINS (HTTPS URLs)
- [ ] Configure production DATABASE_URL
- [ ] Enable HTTPS/SSL
- [ ] Configure reverse proxy (nginx, ALB, etc.)
- [ ] Run `python manage.py check --deploy`
- [ ] Test with production-like environment
- [ ] Review security headers
- [ ] Set up monitoring/logging
- [ ] Configure backup strategy

## Reverse Proxy Setup

If using nginx, add to your config:

```nginx
location / {
    proxy_pass http://backend:8000;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Host $server_name;
    proxy_set_header Host $host;
}
```

Then uncomment in settings.py:

```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

## Migration: Old SECRET_KEY to New

If changing SECRET_KEY, all JWT tokens will be invalidated. Plan for:

1. Communicate to users beforehand
2. Deploy during low-traffic period
3. Users will need to re-login
4. Consider transition period with both keys

## Files Changed

- `requirements.txt` - Added python-dotenv
- `backend/settings.py` - All security configuration
- `docker-compose.yml` - Fixed DJANGO_SETTINGS_MODULE path
- `.env.example` - Template for local development
- `.env.docker.example` - Template for Docker
- `.env.docker` - Local Docker development config

## Additional Resources

- [Django Security](https://docs.djangoproject.com/en/6.0/topics/security/)
- [Django Settings](https://docs.djangoproject.com/en/6.0/ref/settings/)
- [OWASP Django Security](https://cheatsheetseries.owasp.org/cheatsheets/Django_Security_Cheat_Sheet.html)
