# Render Deployment Guide

This document provides the recommended configuration for deploying this Django project on Render.

## Current Setup Status

✅ **Already Configured:**

- WhiteNoise middleware installed and enabled for static file serving
- `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'` set in `settings.py`
- Health check endpoint (`/healthz/`) available
- Gunicorn start command in use

## Recommended Render Configuration

### Build Command

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**What it does:**

- Installs all Python dependencies
- Collects and compresses static files at build time (faster than collecting at runtime)

### Start Command

```bash
gunicorn skb.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 30 --access-logfile -
```

**What it does:**

- Binds to Render's dynamic `$PORT` environment variable
- Uses 2 workers (suitable for free tier; adjust to 3-4 for paid plans)
- Sets 30-second timeout for long requests
- Logs access for debugging

### Health Check Configuration

In Render Dashboard → Service → Health Checks:

| Setting                   | Value                                |
| ------------------------- | ------------------------------------ |
| **Health Check Path**     | `/healthz/`                          |
| **Health Check Protocol** | HTTP                                 |
| **Port**                  | Leave blank (uses default HTTP port) |
| **Initial Delay**         | 30 seconds                           |
| **Interval**              | 60 seconds                           |
| **Timeout**               | 5 seconds                            |

**Why this helps:**

- Render waits for the app to respond 200 OK from `/healthz/` before declaring the service ready
- Eliminates (or greatly reduces) the "APPLICATION LOADING / SERVICE WAKING UP" splash screen
- Ensures your DB migrations and app initialization complete before Render starts routing traffic

## Environment Variables

Add these in Render Dashboard → Service → Environment:

| Key             | Value                   | Notes                                               |
| --------------- | ----------------------- | --------------------------------------------------- |
| `DEBUG`         | `False`                 | Always disable in production                        |
| `ALLOWED_HOSTS` | `skb-bank.onrender.com` | Your Render domain                                  |
| `SECRET_KEY`    | _(rotate this)_         | Use a strong random key, not the one in settings.py |

## Cold Start & Performance Tips

1. **Database:** SQLite works for free tier, but consider PostgreSQL for better concurrency.
2. **Static Files:** WhiteNoise compresses and caches CSS/JS at build time → instant load.
3. **Workers:** 2 workers = 2 concurrent requests. Increase if you see timeout errors.
4. **Timeout:** 30 seconds is standard; increase to 60+ if migrations/heavy tasks run at startup.
5. **Monitoring:** Check Render's logs after deploy to see cold-start times and any errors.

## Typical Cold Start Timeline

- **0s:** Render starts container
- **2-5s:** Python/dependencies load
- **5-10s:** Django imports and migrations apply
- **10-12s:** Gunicorn ready, `/healthz/` returns 200
- **12s+:** Render routes traffic; app responds immediately

If the splash screen persists >15s, check:

- Render logs for slow migrations or imports
- Build output for collectstatic issues
- Worker/timeout settings

## Quick Deploy Checklist

- [ ] Push this code to your Git remote (GitHub, GitLab, etc.)
- [ ] Render detects push; Build Command runs
- [ ] Set Start Command to the gunicorn command above
- [ ] Configure Health Check with `/healthz/` path
- [ ] Set `DEBUG=False` and `SECRET_KEY` env vars
- [ ] Check logs after deploy for any errors
- [ ] Visit your domain and verify app loads quickly

---

For more info: [Render Django Deployment Docs](https://render.com/docs/deploy-django)
