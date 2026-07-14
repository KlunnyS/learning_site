# NihongoPath

NihongoPath is a Flask study tracker for Japanese learners. It tracks kana, kanji, vocabulary, grammar, reading, listening, writing, SRS reviews, mistakes, XP, levels, and study progress.

## Screenshots

Screenshots can be added after the first UI pass.

## Setup

```bash
cp .env.example .env
python run.py
```

`python run.py` creates `.venv` if needed, installs `requirements.txt`, initializes the database tables, loads starter content when the database is empty, and starts the Flask development server.

Open `http://127.0.0.1:5000`.

The first registered user is made an admin for local development.

## Database

The default SQLite database is `instance/nihongopath.db`. Initialize or recreate tables with:

```bash
flask --app run.py init-db
python seed.py
```

`seed.py` is idempotent and can be run repeatedly without duplicating learning items.

## Tests

```bash
.venv/bin/python -m pytest
```

Tests use a temporary SQLite database.

## Project Structure

- `app/__init__.py` app factory and blueprint registration
- `app/models/` SQLAlchemy models
- `app/routes/` auth, main app, and admin routes
- `app/services/` SRS and recommendations
- `app/templates/` Jinja templates
- `app/static/` CSS and JavaScript
- `seed.py` starter content loader
- `docs/` developer notes

## Main Features

- Registration, login, logout, onboarding, and protected study routes
- Seeded hiragana, katakana, starter vocabulary, kanji, grammar, writing, reading, listening, and conjugation content
- Generic lessons with progress actions
- SRS reviews with mistake logging
- Dashboard recommendations, progress charts, notebook, and admin content management
