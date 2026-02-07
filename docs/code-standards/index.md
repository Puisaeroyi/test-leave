# Code Standards & Guidelines

**Last Updated:** 2026-02-07 | **Version:** 1.1.0

This document series defines coding conventions, architectural patterns, and quality standards for the Leave Management System.

## Core Principles

1. **YAGNI** - Don't implement features until they're needed
2. **KISS** - Prefer simple, readable code over clever solutions
3. **DRY** - Extract common logic into reusable functions/components
4. **SOLID** - Design principles for maintainability
5. **Testing First** - Write tests alongside implementation
6. **Documentation** - Code should be self-documenting

## Contents

- [Backend Standards](./backend-standards.md) - Django/Python conventions
- [Frontend Standards](./frontend-standards.md) - React/TypeScript conventions
- [Git & Version Control](./git-version-control.md) - Commit messages, branching
- [Testing Guidelines](./testing-guidelines.md) - Unit, integration, E2E tests
- [Performance Guidelines](./performance-guidelines.md) - Optimization strategies
- [Security Guidelines](./security-guidelines.md) - Best practices

## Quick Reference

**Backend:** Python 3.12, Django 6.0, DRF 3.14, PostgreSQL 16
**Frontend:** React 19, TypeScript 5.9, Vite 7.2, Ant Design 6.2

**Max file size:** 200 LOC (split larger files)
**Test coverage target:** Backend 80%, Frontend 70%
**Code review:** All PRs require review before merge

---

*For detailed codebase information, see [../codebase-summary.md](../codebase-summary.md).*
