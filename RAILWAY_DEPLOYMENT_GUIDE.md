# 🚀 Railway Deployment Guide

## Quick Start: Deploy to Railway

### Prerequisites
- GitHub account (✅ Done - your repo is ready)
- Railway account (create at https://railway.app)
- Your GitHub repo: `https://github.com/operationsmuntech-star/schoolsys.git`

---

## Step 1: Create Railway Project

1. **Go to Railway.app**
   - Visit: https://railway.app
   - Click "Start a New Project"

2. **Deploy from GitHub**
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub account
   - Select repository: `operationsmuntech-star/schoolsys`

3. **Railway Auto-Detects**
   - Detects Django project (from `requirements.txt` and `manage.py`)
   - Detects Procfile configuration
   - Sets up environment automatically

---

## Step 2: Configure Environment Variables

Railway will prompt for environment variables. Add these:

### Required (Railway will set automatically or prompt):
```
# Railway provides these automatically:
DATABASE_URL=postgresql://...  # Provided by Railway Postgres
SECRET_KEY=your-secret-key     # Set a secure value
DEBUG=False                     # Never True in production
ALLOWED_HOSTS=*.railway.app

# For multi-tenant:
CORS_ALLOWED_ORIGINS=https://yourdomain.railway.app

# JWT Settings (optional, use defaults):
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
```

### How to Set in Railway:
1. Go to Project → Variables
2. Click "Add Variable"
3. Set key/value pairs
4. Redeploy for changes

---

## Step 3: Add PostgreSQL Database

1. **In Railway Dashboard**
   - Click "+ New" in top-right
   - Select "Database"
   - Choose "PostgreSQL"

2. **Connect to Django**
   - Railway auto-creates `DATABASE_URL`
   - Django automatically uses it from `settings.py`

3. **Run Migrations**
   - After deployment, run migrations via Railway CLI:
   ```bash
   railway run python manage.py migrate
   ```

---

## Step 4: Deploy

### Auto-Deploy (Recommended)
- Railway automatically deploys when you push to `master` branch
- You'll see deployment status in Railway dashboard
- Takes ~2-3 minutes

### Manual Deploy
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Deploy
railway up
```

---

## Step 5: Initialize Data

After deployment is live, initialize your data:

```bash
# Via Railway CLI
railway run python manage.py create_test_schools

# Or via Railway Dashboard > Deployments > SSH > Terminal
python manage.py migrate
python manage.py create_test_schools
```

---

## Verify Deployment

1. **Check Deployment Status**
   - Railway Dashboard → Deployments
   - Green checkmark = Success ✓

2. **Test Your API**
   ```bash
   curl https://your-project.railway.app/api/v1/auth/schools/
   ```

3. **Test Login**
   - Visit: `https://your-project.railway.app/views/login.html`
   - Use test credentials:
     - School Code: `SCHOOL_A` or `DEMO`
     - Username: `teacher_a` or `demo_user`
     - Password: `demo123`

4. **Check Logs**
   - Railway Dashboard → Deployments → Logs
   - Look for migrations success
   - Verify no critical errors

---

## File Reference

### Railway Configuration Files
- **`Procfile`** - Tells Railway how to start the app
  ```
  web: gunicorn backend.config.wsgi --log-file -
  release: python manage.py migrate
  ```

- **`railway.toml`** - Railway-specific settings (optional)
  ```toml
  [build]
  builder = "nixpacks"

  [deploy]
  startCommand = "gunicorn backend.config.wsgi"
  ```

- **`requirements.txt`** - Python dependencies
  - Already configured with Django, DRF, Gunicorn, etc.

### Django Configuration
- **`backend/config/settings.py`**
  - Auto-reads `DATABASE_URL` environment variable
  - Auto-reads `ALLOWED_HOSTS` from Railway
  - Uses `DEBUG` environment variable

---

## Production Checklist

- [ ] PostgreSQL database created
- [ ] Environment variables set
- [ ] Migrations run successfully
- [ ] Test users created
- [ ] Login page accessible
- [ ] API endpoints responding
- [ ] Static files serving
- [ ] Logs show no errors
- [ ] CORS configured
- [ ] JWT tokens working
- [ ] Multi-tenant isolation verified

---

## Troubleshooting

### Deployment Fails
**Check:**
1. Railway Logs: Dashboard → Deployments → Logs
2. Common issues:
   - Missing `requirements.txt`
   - Syntax errors in Python
   - Missing environment variables
   - Database connection failed

**Fix:**
```bash
# Check locally first
python manage.py runserver

# Check requirements
cat requirements.txt | grep -E "Django|gunicorn"
```

### 502 Bad Gateway
**Likely:** App crashed or database not connected

**Fix:**
1. Check Railway logs
2. Verify DATABASE_URL is set
3. Run migrations: `railway run python manage.py migrate`
4. Restart deployment: Dashboard → Restart

### Static Files Not Loading
**Railway serves static files automatically**

If missing:
```bash
# Collect static files (Railway does this automatically, but can be manual)
railway run python manage.py collectstatic --noinput
```

### Database Connection Failed
```
Error: connect ECONNREFUSED

Fix:
1. Verify PostgreSQL service is running (Railway Postgres added?)
2. Check DATABASE_URL is set in variables
3. Manually add Postgres: "+ New" → "Database" → "PostgreSQL"
```

---

## Monitoring & Logs

### View Logs
1. **Railway Dashboard**
   - Deployments → Select deployment → Logs
   - Real-time streaming

2. **CLI**
   ```bash
   railway logs
   ```

### Important Log Markers
- ✅ `Starting server`: App starting
- ✅ `Migrations applied`: Database migrations done
- ⚠️ `[WARNING]`: Check these messages
- ❌ `[ERROR]`: Critical issues

---

## Next Steps After Deployment

### 1. Create Schools
```bash
railway run python manage.py create_test_schools
# or manually in Django admin
```

### 2. Set Up Domain (Optional)
```
1. Dashboard → Project Settings
2. Add Custom Domain
3. Point DNS to Railway
4. Enable HTTPS (automatic)
```

### 3. Add Collaborators (Optional)
```
1. Dashboard → Settings → Members
2. Invite team members
3. Set permissions (admin/viewer)
```

### 4. Set Up Monitoring (Optional)
```
1. Dashboard → Observability
2. Enable error tracking
3. Enable performance monitoring
```

---

## Environment Variables Reference

### Required for Production
```bash
# Django
SECRET_KEY=your-very-secret-key-here-min-50-chars
DEBUG=False
ALLOWED_HOSTS=your-project.railway.app

# Database (Railway sets automatically)
DATABASE_URL=postgresql://user:pass@host:5432/db

# CORS (Multi-tenant)
CORS_ALLOWED_ORIGINS=https://your-project.railway.app

# Optional: Custom settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Set in Railway
```
1. Dashboard → Variables
2. Add each variable
3. Click Redeploy
```

---

## Deployment Info Display

After successful deployment, you'll have:

```
🚀 Railway Deployment Ready!

URL: https://your-project.railway.app
API: https://your-project.railway.app/api/v1/
Frontend: https://your-project.railway.app/
Login: https://your-project.railway.app/views/login.html

Database: PostgreSQL (Railway Postgres)
Status: ✅ Live & Running
Logs: Available in Railway Dashboard
```

---

## Update & Redeploy

### Push Code Changes
```bash
# Make changes locally
git add .
git commit -m "Your message"
git push origin master

# Railway auto-deploys!
# Watch Dashboard → Deployments
```

### Manual Redeploy (if needed)
```bash
railway up
```

---

## Additional Resources

- Railway Docs: https://docs.railway.app
- Django Deployment: https://docs.railway.app/guides/django
- Railway CLI: https://docs.railway.app/cli/installation

---

## Support

### If Deployment Fails
1. Check Railway Logs
2. Review environment variables
3. Check requirements.txt
4. Test locally: `python manage.py runserver`
5. See Troubleshooting section above

### Common Commands
```bash
# View logs
railway logs

# Run command on deployed app
railway run python manage.py migrate

# Connect to database
railway connect

# Redeploy
railway up

# View project info
railway status
```

---

**Your app is now ready to deploy to Railway!** 🚀

Next: Visit https://railway.app and follow Step 1 above.
