# Railway Deployment Fix – schoolos.up.railway.app 404 Error

## Problem Identified
The 404 error on your Railway domain was caused by:
1. **Frontend files not collected** during the `collectstatic` build step
2. **Incorrect file path resolution** when Django tried to serve `index.html`
3. **Static assets (scripts, styles) not being served** properly in production
4. **Health check endpoint** pointing to `/admin/login/` instead of `/health/`

## Changes Applied

### 1. **Updated `backend/config/settings.py`**
   - Added `STATICFILES_DIRS` to include the `frontend/` folder in static file collection
   - Now `python manage.py collectstatic` will copy all frontend files to `staticfiles/`

### 2. **Enhanced `backend/core/views.py`**
   - Updated `spa_index()` view to check multiple paths:
     - Local dev: `frontend/index.html`
     - Production: `staticfiles/index.html`
   - Now includes error diagnostics if files are not found

### 3. **Improved `backend/config/urls.py`**
   - Added explicit routes for frontend assets: `scripts/`, `styles/`, `views/`, `components/`
   - Uses Django's `serve()` view to properly handle static file serving
   - Routes `manifest.json` and `offline.html` correctly

### 4. **Fixed `railway.toml`**
   - Build: Added `--clear` flag to `collectstatic` to ensure clean builds
   - Deploy: Uses `/health/` endpoint (simple 200 response) instead of `/admin/login/`
   - Added worker count for better performance

### 5. **Updated `Procfile`**
   - Now runs `collectstatic` before Gunicorn starts
   - Consistent with Railway deployment settings

## Deployment Steps

### On Railway:
1. **Push your changes** to the branch connected to Railway
2. Railway will:
   - Install dependencies from `requirements.txt`
   - Run `python manage.py migrate` (sets up database)
   - Run `python manage.py collectstatic --noinput --clear` (copies frontend files)
   - Start Gunicorn with the WSGI app

### Local Testing (Before Deploying):
```bash
# Simulate the production build process
python manage.py collectstatic --noinput --clear

# Run the dev server
python manage.py runserver

# Test the app
# Open http://127.0.0.1:8000/ — should see the MunTech landing page
```

### Verify the Deployment:
```bash
# Check health endpoint
curl https://schoolos.up.railway.app/health/

# Should return: {"status": "ok"}
```

## Environment Variables Required on Railway
Set these in your Railway project settings:

- `SECRET_KEY` — A secure random string (generated from Django)
- `DEBUG` — Set to `False` for production
- `DATABASE_URL` — Auto-configured by Railway when you add Postgres
- `PORT` — Usually `8000` (auto-configured)

## What Each File Does Now

| File | Purpose |
|------|---------|
| `frontend/index.html` | Main SPA entry point (landing/gate page) |
| `frontend/scripts/` | JavaScript modules (auth, db, gate, etc.) |
| `frontend/styles/` | CSS files (tailwind, base, theme) |
| `frontend/views/` | HTML view templates (login, dashboard, etc.) |
| `staticfiles/` | **Production copy** of all frontend files (created by `collectstatic`) |

## Troubleshooting

### Still seeing 404?
1. Check Railway logs:
   - Go to Railway → Logs tab
   - Look for errors during the build phase
   
2. Verify static files were collected:
   - SSH into your Railway container (if available)
   - Run: `ls -la staticfiles/` to see if files are there

3. Check the `spa_index` fallback output:
   - The error response now shows which paths were tried
   - This helps debug file location issues

### Service Worker / Offline not working?
- The service worker is still cached by browsers
- Clear browser cache or use Incognito mode
- Check `/offline.html` is being served correctly

### API requests failing with 401?
- Ensure your `SECURE_PROXY_SSL_HEADER` setting is correct (it is)
- Railway's load balancer adds `X-Forwarded-Proto: https` header
- Django now trusts this header for SSL redirection

## Next Steps

1. **Push to Railway and monitor the deployment**
2. **Test the landing page** at `https://schoolos.up.railway.app/`
3. **Test Sign In flow** — should work with school code/name
4. **Check offline mode** — open DevTools → Network → Offline and test writes
5. **Verify sync badge** when internet returns

---

**If you still see 404 after these changes:**
1. Force a rebuild on Railway (redeploy)
2. Clear your browser cache
3. Check the Railway logs for `collectstatic` errors
4. Run `python manage.py collectstatic --noinput --clear` locally and check the output

Good luck! 🚀
