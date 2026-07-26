# Git Workflow Guide

The rubric rewards a clean history built from feature branches with
meaningful commit messages and merged pull requests. Follow this
sequence to reproduce that history from the finished project.

## 1. Initialize and push the repo

```bash
cd workout-api
git init
git branch -M main
git add .gitignore README.md
git commit -m "chore: initial project scaffold and README"
# create an empty repo on GitHub first, then:
git remote add origin https://github.com/<you>/workout-api.git
git push -u origin main
```

## 2. Build each piece on its own feature branch

Work one concern at a time. For each branch: create it, commit, push,
open a Pull Request on GitHub, then merge it into `main`.

```bash
# Models
git checkout -b feature/models
git add server/config.py server/models.py Pipfile .flaskenv
git commit -m "feat: add Workout, Exercise, and WorkoutExercise models with constraints"
git push -u origin feature/models
# open PR -> merge -> then:
git checkout main && git pull

# Schemas
git checkout -b feature/schemas
git add server/schemas.py
git commit -m "feat: add Marshmallow schemas with validations"
git push -u origin feature/schemas

# Endpoints
git checkout -b feature/endpoints
git add server/routes.py server/app.py
git commit -m "feat: add workout and exercise API endpoints"
git push -u origin feature/endpoints

# Seed data
git checkout -b feature/seed
git add server/seed.py
git commit -m "feat: add seed script for all models"
git push -u origin feature/seed

# Migrations (after running flask db migrate)
git checkout -b feature/migrations
git add migrations/
git commit -m "chore: add initial database migration"
git push -u origin feature/migrations

# Tests
git checkout -b feature/tests
git add tests/
git commit -m "test: add endpoint and validation tests"
git push -u origin feature/tests
```

## 3. Merge and finish

Merge each PR through the GitHub UI (this gives you the "merged
branches / organized PRs" history the rubric looks for). After all
branches are merged:

```bash
git checkout main
git pull
```

## Commit message conventions

Use short, meaningful prefixes so the history reads clearly:

- `feat:` a new feature
- `fix:` a bug fix
- `chore:` tooling / config / scaffolding
- `test:` tests
- `docs:` documentation

## Notes

- `Pipfile.lock` and `*.db` are git-ignored so you don't commit
  environment-specific or generated files.
- Commit the `migrations/` folder (after running `flask db migrate`) so
  graders can run `flask db upgrade` directly.
