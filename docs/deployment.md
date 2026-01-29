# Deployment Guide

## Local Deployment (LAN)

### Requirements
- Python 3.9+
- School network (WiFi or Ethernet)
- One computer as "server"

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Migrate database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run on all network interfaces
python manage.py runserver 0.0.0.0:8000
```

### Access from Other Computers
Find server IP:
```bash
# Windows
ipconfig
# Find IPv4 Address, e.g., 192.168.1.100

# Linux/Mac
ifconfig
```

Other computers access: `http://192.168.1.100:8000`

### Advantages
- ✅ No internet required
- ✅ No monthly costs
- ✅ Complete data control
- ✅ Instant local sync

### Disadvantages
- ❌ Single point of failure
- ❌ Limited to school network
- ⚠️ Manual backups needed

## Cloud Deployment (Railway)

### Prerequisites
- GitHub account
- Railway account (free tier available)
- Environment variables configured

### Setup

1. **Push to GitHub**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Connect Railway**
- Go to railway.app
- Create new project
- Connect GitHub repo
- Select `school-infra`

3. **Configure Environment**
Railway auto-reads `railway.toml`:
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python manage.py migrate && gunicorn backend.config.wsgi"
```

4. **Set Variables**
```
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app,localhost
DATABASE_URL=postgresql://...
```

### Custom Domain
1. In Railway dashboard: Settings → Domain
2. Add custom domain (e.g., `muntech.school`)
3. Update DNS records

### Advantages
- ✅ Always available globally
- ✅ Automatic backups
- ✅ SSL/HTTPS included
- ✅ Auto-scaling
- ✅ PWA can sync globally

### Disadvantages
- ❌ Requires internet
- ❌ Monthly costs ($5-50+)
- ❌ Data on third-party servers

## Hybrid Deployment (LAN + Cloud)

### Best of Both Worlds

**Scenario:**
- Primary: Local school network (offline)
- Secondary: Cloud backup (when online)

```
School Network (LAN)
├── SQLite on server
├── Teachers/Students mark attendance offline
└── When online, sync to Railway

Railway (Cloud)
├── Backup database
├── Multi-school analytics
└── Global sync hub
```

### Setup
1. Deploy locally as above
2. Deploy to Railway
3. Configure sync endpoint in frontend:
```javascript
const API_URL = navigator.onLine 
  ? 'https://muntech.railway.app/api/v1'
  : 'http://192.168.1.100:8000/api/v1';
```

## Database Choices

### SQLite (Default - Phase 0)
```
Pros: Zero setup, no DevOps, file-based
Cons: Limited concurrent users (< 50)
Best for: Single school
```

### PostgreSQL (Production - Phase 1)

```bash
# In railway.toml
[build]
nixPackages = ["postgresql"]

# In settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', 5432),
    }
}
```

### MySQL (Alternative)
Similar to PostgreSQL, replace `django.db.backends.mysql`

## Backups

### Local (SQLite)
```bash
# Copy database
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3

# Automated (crontab)
0 2 * * * cp /path/to/db.sqlite3 /backups/db_$(date +\%Y\%m\%d).sqlite3
```

### Cloud (PostgreSQL)
- Railway auto-backups
- Or use: `pg_dump -U user dbname > backup.sql`

## Monitoring

### Health Check
```bash
curl https://muntech.railway.app/api/v1/health/
# {"status": "ok"}
```

### Logs
```bash
# Local
python manage.py runserver --verbosity 2

# Railway
railway logs
```

## Security Checklist

- [ ] `SECRET_KEY` is strong random string
- [ ] `DEBUG = False` in production
- [ ] `ALLOWED_HOSTS` configured
- [ ] Database password is strong
- [ ] HTTPS enabled (free on Railway)
- [ ] CORS configured for your domain
- [ ] Static files served by CDN (optional)
- [ ] Rate limiting enabled
- [ ] Admin URL protected/hidden

## Troubleshooting

### "Offline but Sync Failing"
- Check `ALLOWED_HOSTS` in settings.py
- Verify network connectivity
- Check browser console for CORS errors

### "Database Locked"
- Kill other Django processes
- Restart server
- Switch to PostgreSQL for multi-user

### "Static Files Missing"
```bash
python manage.py collectstatic --noinput
# Make sure STATIC_ROOT is set
```

---

**Start local. Add cloud when needed.**
