# Git & Version Control Standards

**Last Updated:** 2026-02-07

---

## Commit Message Format

Follow Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring (no functionality change)
- `test:` Adding or updating tests
- `perf:` Performance improvement
- `chore:` Dependencies, config, etc.
- `ci:` CI/CD changes
- `style:` Code style (formatting, missing semicolons)

### Examples

```
feat(leaves): add dynamic EXEMPT_VACATION allocation by YoS

Implement tiered allocation based on years of service:
- Year 1: Prorated (8h/month)
- Years 2-5: 80 hours
- Years 6-10: 120 hours
- Years 11-15: 160 hours
- Years 16+: 200 hours

Reference calculation uses join_date and reference_date (Jan 1).
Fixes #45

feat(frontend): implement business trip calendar view
fix(auth): correct JWT token expiration calculation
refactor(leaves): extract working day calculation to utils
docs: update README with new feature overview
test(approval): add atomic transaction tests
perf(api): optimize leave request query with select_related
```

### Subject Line Rules

- Use imperative mood ("add" not "added" or "adds")
- Don't capitalize first letter
- No period at the end
- Max 50 characters
- Describe what the code does, not why

### Body Guidelines

- Wrap at 72 characters
- Explain "why" not "what"
- Include context and consequences
- Separate from subject with blank line

### Footer

Reference issues and breaking changes:

```
Fixes #123
Closes #456
BREAKING CHANGE: API endpoints now require authentication
```

---

## Branch Naming

```
feature/user-description         # New features
bugfix/issue-description         # Bug fixes
refactor/component-name          # Refactoring
docs/section-name               # Documentation
hotfix/urgent-fix-description   # Production hotfixes
chore/dependency-updates        # Dependency updates
```

### Examples

```
feature/dynamic-vacation-allocation
bugfix/jwt-token-expiration-issue
refactor/leave-approval-service
docs/system-architecture-diagrams
hotfix/database-connection-pool-leak
```

---

## Pull Request Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Keep commits focused and logical
- Use type hints, docstrings, tests
- Follow code standards

### 3. Pre-commit Checks

```bash
# Backend linting
flake8 . --exclude=venv

# Backend tests
python -m pytest --verbosity=2

# Frontend linting
cd frontend && npm run lint

# Frontend type checking
cd frontend && npx tsc --noEmit
```

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
```

### 5. Code Review Checklist

Before merging, verify:

- [ ] Code follows style guidelines (PEP 8, ESLint)
- [ ] Tests pass locally and in CI/CD
- [ ] New code has corresponding tests
- [ ] No sensitive data committed (.env, secrets)
- [ ] Documentation updated (README, docstrings)
- [ ] Database migrations tested
- [ ] No console errors or warnings
- [ ] Performance impact considered
- [ ] Security implications reviewed
- [ ] Commit messages follow convention

---

## Merge Strategies

### Squash & Merge (Preferred)

For feature branches with multiple commits:

```bash
git merge --squash feature/your-feature-name
git commit -m "feat(module): clear description"
```

### Linear History (for complex features)

```bash
git merge --no-ff feature/your-feature-name
```

### Fast-Forward (for single commits)

```bash
git merge feature/your-feature-name
```

---

## Handling Sensitive Data

### NEVER Commit:
- `.env` files with secrets
- API keys, passwords, tokens
- Private certificates
- Database credentials
- Confidential configuration

### If Accidentally Committed:

```bash
# Remove from git history (use with caution)
git rm --cached .env
echo ".env" >> .gitignore
git commit --amend --no-edit
git push --force-with-lease
```

### Use Environment Variables

```bash
# .env.example (safe to commit)
DEBUG=False
SECRET_KEY=change-this-in-production
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# .env (in .gitignore)
DEBUG=False
SECRET_KEY=your-actual-secret-key
DATABASE_URL=postgresql://prod_user:prod_pass@prod_db:5432/db
```

---

## Rebasing & Conflict Resolution

### Keep Branch Updated

```bash
git fetch origin
git rebase origin/main
```

### Interactive Rebase (Clean History)

```bash
git rebase -i origin/main

# In editor:
# pick - use commit
# reword - use commit, edit message
# squash - use commit, meld with previous
# fixup - like squash, discard log message
# drop - remove commit
```

### Resolve Conflicts

```bash
# Edit files to resolve conflicts
# Remove conflict markers (<<<<, ====, >>>>)

git add resolved_file.py
git rebase --continue

# To abort
git rebase --abort
```

---

## Releasing & Tagging

### Version Numbering (Semantic Versioning)

```
MAJOR.MINOR.PATCH
v1.1.0

Major: Breaking changes
Minor: New features (backward compatible)
Patch: Bug fixes
```

### Creating Release Tags

```bash
# Tag current commit
git tag -a v1.1.0 -m "Version 1.1.0 - Phase 2 Milestone 1"

# Tag previous commit
git tag -a v1.0.0 -m "Version 1.0.0" abc1234

# Push tags
git push origin --tags
```

### Release Checklist

- [ ] All tests passing
- [ ] Code review complete
- [ ] Changelog updated
- [ ] Documentation updated
- [ ] Version number bumped
- [ ] Tag created and pushed
- [ ] Release notes prepared

---

## Collaboration Best Practices

### Before Starting Work

```bash
git pull origin main
git checkout -b feature/your-feature
```

### During Development

Keep commits logical and focused:

```bash
# Good
git commit -m "feat(auth): implement JWT token refresh"
git commit -m "test(auth): add token refresh unit tests"

# Avoid
git commit -m "fix: stuff and things" # Unclear
git commit -am "." # No message
```

### Code Review Communication

- **Be respectful:** "Consider using..." not "This is wrong"
- **Be specific:** Link to lines, explain reasoning
- **Be prompt:** Review within 24 hours
- **Approve clearly:** "LGTM" or "Approved" when satisfied

---

## Common Git Commands

```bash
# View commit history
git log --oneline -10
git log --graph --oneline --all

# View changes
git diff main..feature/branch
git show commit-hash

# Stash work in progress
git stash
git stash pop

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Reset to remote state (discard changes)
git reset --hard origin/main

# Find commit by keyword
git log --grep="keyword"

# Blame (find who changed what)
git blame path/to/file.py
```

---

## CI/CD Integration

All commits trigger:

1. **Linting:** Code style checks
2. **Testing:** Unit and integration tests
3. **Coverage:** Report code coverage
4. **Build:** Build Docker images
5. **Security:** Scan for vulnerabilities

View CI/CD status in pull request checks before merging.

---

## Troubleshooting

**Accidentally committed to main:**
```bash
git revert commit-hash
# or cherry-pick to new branch
git checkout -b feature/fix
git cherry-pick commit-hash
```

**Need to undo published commit:**
```bash
git revert commit-hash  # Create new commit that undoes changes
git push origin main
```

**Lost commits:**
```bash
git reflog  # Find lost commits
git checkout commit-hash  # Recover
```

---

*Follow these standards to maintain clean, professional git history and smooth collaboration.*
