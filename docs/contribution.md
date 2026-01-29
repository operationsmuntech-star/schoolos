# Contributing Guide

## Welcome!

MunTech School Infrastructure is open source and welcomes contributions from developers, educators, and schools.

## Getting Started

### Prerequisites
- Python 3.9+
- Git
- Basic Django knowledge helpful (not required)

### Local Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/school-infra.git
cd school-infra

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

## Code Style

### Python (Backend)
- Follow PEP 8
- Use 4 spaces for indentation
- Format with Black: `black backend/`
- Lint with Pylint: `pylint backend/`

### JavaScript (Frontend)
- Use 2 spaces for indentation
- Use const/let, not var
- Use arrow functions
- Format with Prettier: `prettier --write frontend/`

## Git Workflow

1. **Create feature branch**
```bash
git checkout -b feature/attendance-ui
# Or: git checkout -b fix/sync-bug
# Or: git checkout -b docs/offline-guide
```

2. **Make changes**
- Add tests if backend logic
- Update docs if new features
- Commit with clear messages

3. **Push and pull request**
```bash
git push origin feature/attendance-ui
# Then create PR on GitHub
```

### Commit Messages
```
feat: Add student roster import
fix: Resolve sync queue deadlock
docs: Update deployment guide
test: Add attendance service tests
refactor: Simplify router logic
```

## Branch Naming

- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation
- `test/*` - Tests
- `refactor/*` - Code improvements

## Testing

### Backend
```bash
python manage.py test

# Specific app
python manage.py test backend.core

# With coverage
coverage run --source='.' manage.py test
coverage report
```

### Frontend
```bash
# Manual testing in DevTools
# Eventually: Jest tests
```

## What to Contribute

### ✅ Welcome
- Bug fixes
- Performance improvements
- New features (on roadmap)
- Documentation
- Translations
- School case studies

### ⚠️ Discuss First
- Major architectural changes
- New dependencies
- Plugin system changes
- Breaking API changes

Create an Issue first to discuss.

## Roadmap Issues

### Phase 1 (Attendance Focus)
- [ ] Student bulk import
- [ ] Attendance reporting
- [ ] Class-level sync
- [ ] SMS notifications (optional)

### Phase 2 (Academics)
- [ ] Grade recording
- [ ] Transcript generation
- [ ] Performance analytics

### Phase 3 (Extensibility)
- [ ] Plugin system
- [ ] Custom reports
- [ ] Third-party integrations

## Translation

Help translate UI to local languages:

1. Extract strings:
```bash
python manage.py makemessages -l swahili
```

2. Edit `locale/sw/LC_MESSAGES/django.po`

3. Compile:
```bash
python manage.py compilemessages
```

## Reporting Issues

### Bug Report Template
```
## Description
[Clear description]

## Steps to Reproduce
1. First step
2. Second step

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- OS: Windows/Mac/Linux
- Browser: Chrome/Firefox/Safari
- Version: 0.1.0
```

### Feature Request Template
```
## Problem
[Why is this needed?]

## Solution
[How should it work?]

## Context
[Any examples or use cases?]
```

## Documentation

### How to Document
- Write in Markdown
- Use code examples
- Link to related docs
- Keep sentences short

### Doc Locations
- `/docs` - Architecture, guides
- Code comments - Complex logic
- Docstrings - Functions/classes
- README.md - Quick start

### Example Docstring
```python
def calculate_attendance_rate(student, term=None):
    """
    Calculate student attendance percentage for a term.
    
    Args:
        student (Student): The student to calculate for
        term (Term, optional): Specific term. Defaults to current.
    
    Returns:
        float: Attendance percentage (0-100)
    
    Raises:
        Student.DoesNotExist: If student not found
    """
    pass
```

## Community

- **Discord**: [Join](https://discord.gg/muntech) (coming soon)
- **Email**: hello@muntech.school
- **Twitter**: @muntechschool
- **Issues**: GitHub Issues

## Code Review

We review all PRs for:
- ✅ Code quality
- ✅ Tests included
- ✅ Documentation updated
- ✅ No breaking changes
- ✅ Performance impact

Be patient - we volunteer and contribute evenings/weekends.

## License

By contributing, you agree your code is licensed under MIT.

---

**Every contribution, big or small, helps schools around Africa.**

Thank you! 🙏
