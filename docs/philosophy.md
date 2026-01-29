# Philosophy - Design Principles

## Core Beliefs

### 1. **People First, Not Users**
We use `people/` not `users/` because schools deal with humans: students, teachers, guardians, staff.

### 2. **Offline Is First, Not Fallback**
The app must work perfectly offline. Online is bonus sync, not requirement.

### 3. **Sacred Core**
Core models (School, Term, Class, Subject) are immutable. All else is plugins.

### 4. **Attendance Is First-Class**
Not a bolt-on feature. Deeply integrated from day one.

### 5. **Sync Beats Proprietary**
We built sync infrastructure day 1 (unlike Zeraki) to avoid vendor lock-in.

## Design Decisions

### Why Django + DRF?
- Batteries included (auth, admin, ORM)
- Perfect for Africa (low bandwidth, async-friendly)
- Large East African community

### Why PWA Over Native?
- Single codebase (web + mobile + desktop)
- No app stores
- Instant updates
- Works on any browser

### Why IndexedDB + SQLite?
- IndexedDB: Client-side offline storage
- SQLite: Server-side, zero DevOps
- Perfect for schools with limited IT

### Why LAN-First, Cloud-Optional?
- Internet is unreliable in rural Kenya/Uganda
- Schools have local networks
- Cloud is sync hub, not requirement

## "Humans First" Philosophy

```
School (org)
├── Term (season)
├── Class (group)
└── Subject (topic)

People
├── Student (learner)
├── Teacher (educator)
├── Guardian (parent/carer)
└── Staff (support)

Attendance (daily rhythm)
│
Sync (optional heartbeat)
```

Not:
```
User
├── Account
├── Permission
└── Metadata
```

## Why Open Source?

Schools should own their data. No vendor lock-in. No subscriptions. Forever.

## Roadmap Philosophy

1. **Phase 0**: Skeleton (you are here)
2. **Phase 1**: Attendance (core workflow)
3. **Phase 2**: Academics (grades + reporting)
4. **Phase 3**: Plugins (any school can extend)
5. **Phase 4**: Multi-school districts

Not: "Everything at once"
But: "Perfect one thing, expand carefully"
