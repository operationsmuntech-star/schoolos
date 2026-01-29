# Roadmap - Future Directions

## Vision

Build the open-source school management system for Africa.

```
Phase 0 (2026 Q1) ✅ Skeleton
   ↓
Phase 1 (2026 Q2) Attendance ← YOU ARE HERE
   ↓
Phase 2 (2026 Q3-Q4) Academics
   ↓
Phase 3 (2027 Q1) Extensibility
   ↓
Phase 4 (2027 Q2+) Districts & Scale
```

## Phase 0: Skeleton ✅

**Status**: Launch ready
- ✅ Django REST backend
- ✅ PWA frontend shell
- ✅ Offline-first caching
- ✅ Sync infrastructure
- ✅ Role-based access
- ✅ Deployable locally + cloud

**Next**: Jump to Phase 1

---

## Phase 1: Attendance (Q2 2026)

**Goal**: Core workflow — marking attendance offline, syncing online

### Features
- [ ] Teacher attendance marking UI
- [ ] Batch student import (CSV)
- [ ] Attendance summaries per student
- [ ] Class-level reports
- [ ] Excused absence tracking
- [ ] Parent SMS notifications (Twilio)
- [ ] Attendance analytics dashboard

### Database
```python
# Additions to models.py
class AttendanceCategory:
    name: str  # "Excused", "Medical", "Family", etc.
    description: str

class AttendanceException:
    student: FK
    date: date
    category: FK
    duration: int  # days
    reason: str

class AttendanceReport:
    class_id: FK
    month: int
    generated_at: datetime
    pdf_url: str
```

### API Endpoints
```
POST   /api/v1/attendance/sessions/
POST   /api/v1/attendance/records/
GET    /api/v1/attendance/reports/?class_id=1&month=1
POST   /api/v1/attendance/bulk-import/
```

### Testing
- [ ] Unit tests for AttendanceEngine
- [ ] Integration tests for sync
- [ ] Load test: 1000 records in session

### Deployment
- [ ] Docker Compose for local deployment
- [ ] PostgreSQL setup for multi-user
- [ ] S3-compatible object storage for reports

---

## Phase 2: Academics (Q3-Q4 2026)

**Goal**: Grades, transcripts, performance analytics

### Features
- [ ] Grade recording (by teacher)
- [ ] Multiple grading scales (A-F, 0-100, etc.)
- [ ] Automatic grade aggregation
- [ ] Transcript generation (PDF)
- [ ] Subject-level analytics
- [ ] Class performance dashboard
- [ ] Student progress tracking
- [ ] Predictive analytics (at-risk students)

### Models
```python
class GradingScale:
    name: str  # "0-100", "A-F", "1-4"
    school: FK
    grades: JSONField

class Grade:
    student: FK
    subject: FK
    term: FK
    score: float
    grading_scale: FK

class Transcript:
    student: FK
    term: FK
    grades: M2M(Grade)
    generated_at: datetime
    pdf_url: str
```

### Reports
- [ ] Student transcript
- [ ] Class performance summary
- [ ] Subject averages
- [ ] Grade distribution

---

## Phase 3: Extensibility (2027 Q1)

**Goal**: Plugins architecture — schools can extend

### Features
- [ ] Plugin system (custom reports, integrations)
- [ ] Custom fields framework
- [ ] Webhook system (send data to external services)
- [ ] Multi-language UI (Swahili, French, etc.)
- [ ] Mobile app wrapper (React Native)
- [ ] API clients (Python, JavaScript)
- [ ] Admin UI improvements

### Plugin Examples
```
plugins/
├── sms-alerts/           # Send SMS for low attendance
├── payroll/              # Teacher salary calculation
├── parents-app/          # Guardian mobile app
├── exam-manager/         # Exam timetable + prep
└── fees-management/      # Fee tracking & receipts
```

---

## Phase 4: Districts & Scale (2027 Q2+)

**Goal**: Multi-school support, centralized management

### Features
- [ ] Multi-school administration
- [ ] Cross-school reporting
- [ ] Centralized user management
- [ ] District-wide analytics
- [ ] Mobile native apps (iOS/Android)
- [ ] Advanced permissions system
- [ ] Real-time collaboration
- [ ] Video conferencing integration

### Infrastructure
- [ ] Kubernetes deployment
- [ ] High-availability database
- [ ] CDN for global reach
- [ ] Real-time sync (WebSocket)

---

## Parallel Initiatives

### Community
- [ ] Local meetups (Nairobi, Kampala, Dar es Salaam)
- [ ] School partnerships for testing
- [ ] Certified administrator training
- [ ] Translation community

### Ecosystem
- [ ] Integration with Zeraki, Strathmore, etc.
- [ ] Open data standards (CEDE, IMS)
- [ ] Government MoE compatibility
- [ ] NGO partnerships

### Sustainability
- [ ] Optional support tier
- [ ] Custom development services
- [ ] Training workshops
- [ ] Certification program

---

## Long-Term Vision (3-5 Years)

```
2026: Every Kenyan school has attendance tracking offline
2027: Multi-school districts use MunTech for complete academics
2028: Open data platform for education analytics
2029: Pan-African school system adoption
2030: 1M+ students using MunTech daily
```

### Success Metrics
- ✅ 1000+ schools deployed
- ✅ 100K+ active students
- ✅ <5 min average sync time
- ✅ 99.9% uptime
- ✅ Zero subscription fees (forever free)

---

## How to Help

### Developers
- Join Phase 1 attendance team
- Contribute bug fixes
- Build plugins

### Schools
- Deploy and test
- Provide feedback
- Share use cases

### Organizations
- Fund development
- Partner for scale
- Train administrators

---

**The future is open, offline-first, and belongs to schools.**
