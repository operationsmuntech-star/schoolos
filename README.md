# MunTech School Infrastructure

A modern, offline-first school management system built for East African schools. Works on mobile and desktop without internet.

## 🎯 Mission

Enable every school in Kenya and East Africa to manage students, attendance, and academics from any device, anytime, anywhere — online or offline.

## ✨ Core Features

- **Offline-First PWA**: Works without internet, syncs when online
- **Attendance Tracking**: Mark and manage daily attendance
- **Student Management**: Register and track student information
- **Academics**: Grade management and performance tracking
- **Multi-role Access**: Students, teachers, guardians, admins
- **Installable Everywhere**: App stores, home screen, desktop
- **LAN Ready**: Deploy on local school network without internet
- **Scalable**: From single school to multi-school districts

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 14+ (for frontend tooling, optional)
- SQLite3 (included with Python)

### Installation

```bash
# Clone repository
git clone https://github.com/muntech/school-infra.git
cd school-infra

# Install backend dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

## 📱 Installation on Devices

### Mobile (Android/iOS)
1. Open app in browser
2. Tap menu → "Add to Home Screen"
3. App works offline

### Desktop
1. Visit in Chrome/Edge
2. Click install icon in address bar
3. Launch as standalone app

## 🏗️ Project Structure

```
school-infra/
├── backend/          # Django REST API (kernel)
│   ├── core/        # School, Term, Class, Subject models
│   ├── people/      # Student, Teacher, Guardian, Staff
│   ├── attendance/  # Attendance tracking
│   ├── sync/        # Offline-first synchronization
│   └── api/         # REST endpoints
├── frontend/        # PWA shell (body)
│   ├── views/       # Dashboard, Attendance, Academics, Settings
│   ├── scripts/     # Service Worker, DB, Sync, Router
│   └── styles/      # Tailwind CSS, theme
└── docs/            # Documentation
```

## 📚 Documentation

- [Philosophy](docs/philosophy.md) - Design principles
- [Offline-First Architecture](docs/offline-first.md) - How offline sync works
- [Deployment](docs/deployment.md) - Deploy to Railway or on-premises
- [Contributing](docs/contribution.md) - How to contribute
- [Roadmap](docs/roadmap.md) - Future features

## 🔄 Phase-Based Development

### Phase 0 ✅
- Core models and API skeleton
- PWA shell with offline caching
- Basic authentication
- Deployment-ready

### Phase 1 (Next)
- Real attendance workflows
- Student roster management
- Complete sync engine
- Teacher/Admin UI

### Phase 2
- Academics/Grades module
- Reports and analytics
- Guardian notifications
- Multi-school support

## 🌍 Deployment

### Local (LAN)
```bash
python manage.py runserver 0.0.0.0:8000
```
Schools can run entirely offline without internet.

### Cloud (Railway)
```bash
railway up
```
See [deployment.md](docs/deployment.md) for details.

## 🔐 Security

- User authentication with token-based auth
- Role-based access control (RBAC)
- CORS configured for PWA
- Data validation on backend
- SQLite default (PostgreSQL recommended for production)

## 🤝 Contributing

See [contribution.md](docs/contribution.md) for guidelines.

## 📄 License

MIT License - See LICENSE file for details

## 👥 Community

- **Target Users**: Schools in Kenya, Uganda, Tanzania, Rwanda
- **Inspiration**: Zeraki Analytics, Eduventure, local solutions
- **Goal**: Open-source alternative to proprietary SaaS

---

**Built for schools that run on battery and hope.** 🌍
