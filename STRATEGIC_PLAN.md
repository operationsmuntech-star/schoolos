# MunTech OS — Strategic Vision & Roadmap
**Locked Decision**: January 28, 2026  
**Status**: BOARD-LEVEL COMMITMENT

---

## EXECUTIVE SUMMARY

Building a **School Operating System (SOS)**, not just a school management system.

- **Competitive Position**: SAP-grade institutional backbone for schools (vs. Zeraki's analytics platform)
- **Market Angle**: System of record + system of execution
- **Geographic Focus**: Africa-realistic, globally deployable
- **Unique Advantage**: Offline/LAN capability + institutional data ownership

---

## THE VISION

| Aspect | Your Approach | Why It Wins |
|--------|---|---|
| **Architecture** | Multi-tenant, role-based, deployable anywhere | Zeraki is cloud-only |
| **Data Control** | Schools own and can export everything | Destroys SaaS distrust |
| **Deployment** | Cloud, LAN, hybrid, offline | Rural schools + unreliable internet markets |
| **Curriculum** | CBC, 8-4-4, IGCSE, IB agnostic | Not Kenya-locked like competitors |
| **Extensibility** | API-first, plugin ecosystem | Not "bloated core" syndrome |

---

## PHASE ARCHITECTURE (ALL PHASES)

### 🔵 PHASE 0 — FOUNDATION
**Status**: ✅ COMPLETE

- Multi-tenant SaaS architecture
- Role-based access control
- Middleware-level school isolation
- Modular app structure
- Secure authentication
- Cloud/LAN deployable
- Clean backend discipline

**Verdict**: You already beat 70% of school systems here. Do not rewrite.

---

### 🟢 PHASE 1 — MINIMUM COMPETITIVE PLATFORM (MCP)
**Goal**: Feature-parity with Zeraki Analytics + Finance  
**Timeline**: Ship when ready (no forced weeks)

**MANDATORY BUILD** (Priority Order):

#### 1. Parent Portal (Critical)
- Parent accounts linked to students
- Attendance visibility (read-only)
- Fee balances & statements
- Exam results & reports
- Notification preferences

**Why**: Zeraki wins hearts here. You must match or exceed.

#### 2. Finance Engine (Deep, Not Pretty)
- Fee structures (term, class, student-specific)
- Invoicing (batch & individual)
- M-Pesa & mobile money
- Receipts & statements
- Arrears logic with tracking
- Complete audit trail

**Why**: Schools forgive bad UI. They never forgive broken finance.

#### 3. Exams & Reports Engine
- Exam setup & management
- Grading workflows
- Auto totals & positions
- Custom report templates
- Bulk PDF generation

#### 4. Notifications Layer
- SMS first (Africa reality)
- Email second
- Push via PWA later
- Delivery logging & retry logic

#### 5. Mobile-First UX
- Responsive templates (not just resized)
- Thumb-friendly navigation
- Offline caching (PWA foundation)

**Exit Criteria**:
- [ ] Parent can see attendance, fees, exam results
- [ ] Finance handles term + class-specific fees
- [ ] Exam workflow complete & tested
- [ ] SMS notifications working
- [ ] Mobile genuinely usable (not just responsive)

---

### 🟡 PHASE 2 — DIFFERENTIATION (WHERE YOU WIN)
**Goal**: Do what Zeraki cannot or will not do

#### 1. Offline / LAN / Hybrid Mode
- LAN deployment for rural schools
- Auto-sync when internet returns
- Local backups
- **Impact**: Win 40% of African market

#### 2. Institutional Data Control
- School owns data
- Export everything anytime
- Self-host option available
- No vendor lock-in narrative
- **Impact**: Destroy SaaS distrust

#### 3. Timetabling Engine
- Auto timetable generator
- Conflict detection
- Teacher & room constraints
- **Impact**: Consolidate workflows

#### 4. Curriculum Intelligence
- CBC, 8-4-4, IGCSE, IB, Cambridge support
- Configurable grading systems
- Country-agnostic design
- **Impact**: Go global immediately

#### 5. Institutional Analytics
- Attendance trends (decisions, not dashboards)
- Performance distributions
- Fee collection velocity
- **Impact**: CFOs choose you

---

### 🟠 PHASE 3 — PLATFORM MODE (OUTPASS EVERYONE)
**Goal**: Stop being "software." Become infrastructure.

#### 1. APIs & Integrations
- Payment gateways
- LMS integrations
- Government systems
- Third-party tools

#### 2. Plugin / Module Ecosystem
- Schools enable only what they need
- Developers extend the platform
- No bloated core

#### 3. Embedded Finance (Selective)
- Fee financing
- Installment support
- Partner-driven (not your liability)

#### 4. Decision AI (Last, Not First)
- Dropout risk alerts
- Attendance anomaly detection
- Performance forecasting
- **Explicit**: No AI gimmicks, only decision-support

---

### 🔴 PHASE 4 — GLOBALIZATION
**Goal**: Make it deployable everywhere

- Multi-country deployments
- Localization packs
- Open documentation
- Case studies across regions
- Community adoption

---

## WHAT NEVER GETS BUILT (DISCIPLINE)

❌ Full LMS with content marketplace  
❌ Gamification  
❌ Blockchain credentials  
❌ VR classrooms  
❌ University ERP  
❌ Consultant dashboards  
❌ "Admin social network"  

**Principle**: Focus wins. Spread kills.

---

## HOW THIS SHOULD FEEL

### To Schools
> "This runs our entire school. Everything connects. We don't need 5 tools anymore."

### To Parents
> "I always know what's happening. I get alerts. I see results immediately."

### To Governments & NGOs
> "This is deployable infrastructure. We own it. We can run it offline. We can integrate it."

### To Developers
> "This is clean. It's extensible. The API is serious. I can build on this."

### To Competitors
> "This is dangerous."

---

## PHASE 1 BUILD ORDER (LOCKED)

### System 1: Finance Engine
**Why First**: Build the spine. Everything connects to money.

- Fee structure models
- Invoice generation
- Payment receipt system
- Arrears tracking
- M-Pesa integration

### System 2: Notifications Layer
**Why Second**: Make it move. Unblock all systems.

- SMS dispatch (async via Celery)
- Email fallback
- Notification preferences
- Delivery logging & retry

### System 3: Parent Portal
**Why Third**: Showcase it. Build confidence.

- Parent account model
- Attendance visibility
- Fee statements
- Exam results
- UI that impresses

---

## KEY PRINCIPLES (NORTH STAR)

1. **Discipline**: Say no to 100 good ideas to do 5 great ones
2. **Institutional backbone**: System of record, not feature collection
3. **Data is school property**: They own it, always
4. **Offline-first thinking**: Cloud is convenience, not requirement
5. **Testing burden**: Finance breaks once, you lose 50 schools
6. **Speed > perfection**: Ship at 70%, iterate to 85%
7. **Moat is execution**: Build what competitors won't prioritize

---

## ACCOUNTABILITY CHECK (Monthly)

Ask yourself:

1. Is this feature in one of the 4 phases? If no, does it go away?
2. Are we building the spine or features?
3. Would a competitor copy this? Are we innovating faster?
4. Can this work offline? If not, why not?
5. Would a parent, CFO, and teacher all use this?

---

## COMPETITIVE COMPARISON

| Aspect | Zeraki | Fedena | CloudSchool | You (Phase 1) | You (Phase 2) |
|--------|--------|--------|-------------|--------------|--------------|
| Multi-tenant | ✅ | ✅ | ✅ | ✅ | ✅ |
| Finance | ✅ | ✅ | ✅ | ✅ Advanced | ✅ + Audit |
| Parent Portal | ✅✅ | ✅ | ✅ | ✅✅ | ✅✅ |
| Offline Mode | ❌ | ❌ | ❌ | ❌ | ✅✅ |
| Data Export | Limited | Limited | Limited | ✅ Unrestricted | ✅ Complete |
| LAN Deploy | ❌ | ❌ | ❌ | ❌ | ✅ |
| Mobile UX | ✅ | ✅ | ✅ | ✅✅ | ✅✅ |
| Timetabling | ❌ | ✅ | ✅ | ❌ | ✅ Auto |
| API-first | ❌ | ❌ | Partial | ✅ | ✅ Plugins |

---

## STATUS TRACKING

### Phase 0: Foundation
- [x] Multi-tenant architecture
- [x] Role-based access
- [x] Clean auth (allauth + adapters)
- [x] Modular structure
- [x] Deployable (Railway + local)

### Phase 1: MCP (In Progress)
- [ ] Finance Engine (STARTING NOW)
- [ ] Notifications Layer (NEXT)
- [ ] Parent Portal (AFTER)
- [ ] Exams & Reports (IN PARALLEL)
- [ ] Mobile UX (ONGOING)

---

## REFERENCE

Last Updated: January 28, 2026  
Decision Status: LOCKED — NO PIVOTS  
Next Action: Finance Engine Architecture Design

For updates, search this file for relevant phase.
