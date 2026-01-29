# Railway Deployment Guide

## ✅ Fixed Issues

Your code is now ready for Railway deployment. Here's what was fixed:

### 1. Dependencies Fixed ✅
- Updated `djangorestframework-simplejwt` from 5.3.2 to 5.5.1 (available version)
- Updated all dependencies to compatible versions
- Added `dj-database-url` for Railway PostgreSQL URL parsing
- Added `python-dotenv` for environment variables

### 2. Django Settings Updated ✅
- Added WhiteNoise middleware for static files in production
- Configured automatic PostgreSQL detection via `DATABASE_URL`
- Added production security settings
- Configured CORS for Railway domains (`*.railway.app`)
- Added JWT authentication defaults

---

## 🚀 Deploy on Railway (5 minutes)

### Step 1: Connect GitHub Repo
1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "GitHub Repo"
4. Choose: `operationsmuntech-star/schoolsys`
5. Click "Deploy"

### Step 2: Configure Environment Variables
In Railway dashboard → Variables:

```
DEBUG=False
SECRET_KEY=your-secure-secret-key-here
ALLOWED_HOSTS=*.railway.app,your-custom-domain.com
DATABASE_URL=(automatically set by Railway)
```

**Generate SECRET_KEY:**
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Step 3: Add PostgreSQL Plugin
1. Click "Add" → "Marketplace"
2. Search "PostgreSQL"
3. Click "PostgreSQL" → "Add"
4. Railway automatically sets `DATABASE_URL`

### Step 4: Configure Start Command
In Railway settings, set Start Command:
```bash
python manage.py migrate && gunicorn backend.config.wsgi
```

### Step 5: Wait for Deployment
- Railway will build your app (~2-3 minutes)
- Automatic deploy on each GitHub push
- View logs in Railway dashboard

---

## 📊 What Gets Deployed

```
Your Django + DRF + Multi-Tenant System:
├─ Backend API (Django REST Framework)
│  ├─ Multi-tenant auth endpoints
│  ├─ Attendance management
│  ├─ Student/teacher management
│  └─ Complete sync engine
│
├─ PostgreSQL Database (Auto-configured)
│  ├─ All models with school_id FK
│  └─ Complete data isolation
│
├─ Static Files (WhiteNoise)
│  └─ Served from Railway
│
└─ Domain
   └─ auto: *.railway.app
   └─ custom: your-domain.com (optional)
```

---

## ✅ Deployment Checklist

- [x] GitHub repo synced
- [x] requirements.txt fixed
- [x] settings.py updated for production
- [x] DATABASE_URL support added
- [x] WhiteNoise configured
- [x] CORS configured
- [x] Security settings added

---

## 🔗 After Deployment

### Your App URLs:
- **API Base**: `https://your-app.railway.app/api/v1/`
- **Admin**: `https://your-app.railway.app/admin/`
- **Auth Login**: `https://your-app.railway.app/api/v1/auth/school-login/`

### First Steps:
1. Create Django superuser:
   ```bash
   railway exec python manage.py createsuperuser
   ```

2. Create test schools:
   ```bash
   railway exec python manage.py create_test_schools
   ```

3. View app logs:
   - Railway Dashboard → Logs tab

### Monitor Deployment:
- View logs in Railway dashboard
- Check deployment status
- Monitor database connections

---

## 🔐 Production Settings Configured

✅ SSL/HTTPS enforcement (automatic on Railway)
✅ Secure session cookies
✅ CSRF protection
✅ XSS protection headers
✅ Content security policy
✅ Database connection pooling
✅ Static files compression
✅ Multi-tenant isolation

---

## 📝 Quick Test After Deploy

```bash
# Test API is working
curl https://your-app.railway.app/api/v1/auth/current-school/

# Expected response:
# 401 Unauthorized (no auth token - this is correct!)
# Means API is running
```

---

## ⚡ Auto-Deploy on Push

Every time you push to GitHub:
1. Railway automatically detects changes
2. Rebuilds Docker image
3. Runs migrations
4. Deploys new version
5. Zero downtime (usually)

```bash
# Example: Make a change, commit, and push
git add .
git commit -m "Your changes"
git push origin master
# → Railway auto-deploys!
```

---

## 🆘 If Deployment Fails

### Check Error Logs:
1. Go to Railway dashboard
2. Click your project
3. View "Logs" tab
4. Look for error messages

### Common Issues:

**"No matching distribution found for djangorestframework-simplejwt"**
- ✅ FIXED in your requirements.txt

**"ModuleNotFoundError: No module named 'whitenoise'"**
- ✅ Added to requirements.txt

**"Database error"**
- Check DATABASE_URL variable is set
- Railway should auto-set it

**"Static files not loading"**
- WhiteNoise is configured
- Should work automatically

---

## 💾 Database Management

### Access Database:
```bash
# Connect to PostgreSQL
railway connect postgres

# Or use Railway CLI to run migrations
railway exec python manage.py migrate
railway exec python manage.py createsuperuser
```

### Backup Database:
- Railway has automatic daily backups
- Access via Railway dashboard → Data

---

## 🎯 Next: Custom Domain (Optional)

1. Buy domain (GoDaddy, Namecheap, etc.)
2. In Railway: Settings → Domains
3. Add custom domain
4. Update DNS records (instructions provided)
5. SSL certificate auto-generated

---

## 📊 Your System Architecture on Railway

```
┌─────────────────────────────────────────────┐
│         Your Custom Domain (Optional)       │
│      or *.railway.app (auto-provided)       │
└──────────────────┬──────────────────────────┘
                   │ HTTPS/SSL (Free)
┌──────────────────▼──────────────────────────┐
│         Railway Application                 │
├─────────────────────────────────────────────┤
│  Django REST Framework                      │
│  ├─ Multi-Tenant Auth                       │
│  ├─ Attendance APIs                         │
│  ├─ Student/Teacher Management              │
│  └─ Complete Sync Engine                    │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│   PostgreSQL Database (Railway)             │
│   ├─ Schools (Tenants)                      │
│   ├─ Attendance Data (School-isolated)      │
│   ├─ Users & Permissions                    │
│   └─ Complete Multi-Tenant Setup            │
└─────────────────────────────────────────────┘
```

---

## 🎉 Ready to Deploy!

Your app is now **production-ready** on Railway:
- ✅ All dependencies fixed
- ✅ Django configured for production
- ✅ PostgreSQL auto-configured
- ✅ Static files served
- ✅ Multi-tenant ready
- ✅ Security hardened

**Next: Push this to Railway and watch it deploy!** 🚀

---

## 📞 Support

If you have issues:
1. Check Railway logs for error messages
2. Review settings.py configuration
3. Verify DATABASE_URL is set
4. Check requirements.txt for missing packages
5. Review multi-tenant documentation in project

---

**Status: ✅ READY FOR RAILWAY DEPLOYMENT**

Your system will be live at: `https://your-app.railway.app`
