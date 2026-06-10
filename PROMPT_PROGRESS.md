# Prompt Progress

NihongoPath prompt series status as of the current implementation.

| Prompt | Status | Notes |
| --- | --- | --- |
| 1 Base Flask project | Complete | App factory, SQLite, SQLAlchemy, Flask-Login, Flask-Migrate, folders, `run.py`, requirements, README, core pages, Tailwind CDN layout |
| 2 Authentication | Complete | Register, login, logout, password hashing, flash messages, protected routes, auth-aware sidebar |
| 3 Core models | Complete | User, LearningItem, UserProgress, ReviewLog, MistakeLog, StudySession and relationships |
| 4 Seed data | Complete | Idempotent `seed.py` for kana, starter vocab, grammar, kanji, writing, reading, listening, conjugation |
| 5 Dashboard | Complete | Real DB-backed stats, recommendation, skills, due reviews, mistakes, empty states |
| 6 Study Path | Complete | World grouping and progress-driven node states |
| 7 Generic lessons | Complete | `/learn/<slug>` with progress actions and grammar-specific detail rendering |
| 8 Kana module | Complete | Kana grids, filters, practice route, progress, review and mistake logging |
| 9 Grammar module | Complete | Grouped grammar curriculum, source links, grammar detail page |
| 10 Vocabulary module | Complete | Browse and practice vocabulary with tracking |
| 11 Kanji module | Complete | Browse and practice kanji with tracking |
| 12 SRS reviews | Complete | SRS service, due reviews page, mixed review handling |
| 13 Progress page | Complete | Stats, Chart.js charts, skill counts, weak areas, N5 placeholder |
| 14 Notebook | Complete | Mistakes, resolve action, notes create/delete |
| 15 Writing practice | Complete | Writing prompts, attempts, simple feedback, XP and mistake logging |
| 16 Reading practice | Complete | Reading passages with furigana and translation toggles |
| 17 Listening practice | Complete | Listening clips with placeholder audio, transcript and translation |
| 18 Conjugation practice | Complete | Seeded verb prompts and answer checking through practice route |
| 19 Recommendations | Complete | Recommendation service with due, weak, mistake, unseen, low-mastery priorities |
| 20 UI polish | Complete | Shared dark theme, cards, badges, XP/level pills, responsive layout |
| 21 Admin/content | Complete | Admin-only content list, create, edit, delete, search/filter |
| 22 Onboarding | Complete | Goal and level onboarding saved to user |
| 23 Tests | Complete | Pytest coverage for app, auth, seed, progress, SRS, mistakes, admin rejection |
| 24 Documentation | Complete | README and docs for content model, SRS, grammar source policy |
| 25 Integration pass | Complete | Seed, tests, and route smoke checks pass |
