# Codex Prompt Series: Build NihongoPath From Scratch

## Project summary for Codex

We are building a Japanese study tracking website called **NihongoPath**.

It should help users learn and track:

* Hiragana
* Katakana
* Kanji
* Vocabulary
* Grammar
* Reading
* Listening
* Writing
* SRS reviews
* Mistakes
* Study progress

The grammar curriculum should be inspired by Tae Kim’s Guide to Japanese Grammar, but do not copy large copyrighted text. Use our own short explanations, original example sentences, and source links.

The visual style should feel inspired by Nihondex: gamified, modern, dark theme, rounded cards, progress tracking, XP, levels, learning paths, and Japanese-learning dashboard style.

Use Flask, SQLite, SQLAlchemy, Flask-Login, Tailwind CSS, vanilla JavaScript, and Chart.js.

---

# Prompt 1 — Create the base Flask project

Build the initial Flask project structure for a Japanese learning web app called NihongoPath.

Requirements:

1. Create a clean Flask app factory structure.
2. Use SQLite for local development.
3. Use SQLAlchemy.
4. Use Flask-Login.
5. Use Flask-Migrate if appropriate.
6. Use environment variables through a `.env` file.
7. Create base folders:

   * `app/`
   * `app/templates/`
   * `app/static/`
   * `app/static/css/`
   * `app/static/js/`
   * `app/routes/`
   * `app/models/`
   * `app/services/`
   * `app/forms/`
   * `app/data/`
8. Add a basic `run.py`.
9. Add a `requirements.txt`.
10. Add a `README.md` with setup instructions.

Create these first pages:

* `/`
* `/dashboard`
* `/learn`
* `/reviews`
* `/progress`

For now, pages can show placeholder content.

Use Tailwind through CDN for now.

Add a shared `base.html` layout with:

* dark background
* sidebar navigation
* mobile-friendly layout
* app name “NihongoPath”
* navigation links:

  * Dashboard
  * Study Path
  * Kana
  * Kanji
  * Vocabulary
  * Grammar
  * Reading
  * Listening
  * Writing
  * Reviews
  * Progress
  * Notebook

Acceptance criteria:

* `python run.py` starts the app.
* All routes load without errors.
* The layout has a dark Japanese-learning dashboard feel.
* The project structure is clean and ready for more features.

---

# Prompt 2 — Add authentication

Add user authentication to NihongoPath.

Requirements:

1. Create a `User` model with:

   * id
   * username
   * email
   * password_hash
   * xp
   * level
   * streak
   * daily_goal_xp
   * created_at
2. Add registration page.
3. Add login page.
4. Add logout.
5. Protect these pages so only logged-in users can access them:

   * `/dashboard`
   * `/learn`
   * `/reviews`
   * `/progress`
   * all study modules
6. Add password hashing.
7. Add flash messages.
8. Add simple form validation.
9. Update the navbar/sidebar to show login/register when logged out and username/logout when logged in.

Acceptance criteria:

* A user can register.
* A user can log in.
* A user can log out.
* Protected pages redirect to login when not authenticated.
* User data is stored in SQLite.

---

# Prompt 3 — Create core database models

Create the main database models for the Japanese learning platform.

Add these models:

## LearningItem

Fields:

* id
* item_type
  Values: `kana`, `kanji`, `vocabulary`, `grammar`, `reading`, `listening`, `writing_prompt`, `conjugation`
* slug
* title
* japanese
* reading
* meaning
* explanation
* jlpt_level
* difficulty
* source_name
* source_url
* tags
* created_at

## UserProgress

Fields:

* id
* user_id
* learning_item_id
* status
  Values: `unknown`, `seen`, `learning`, `reviewing`, `known`, `weak`, `mastered`, `forgotten`
* mastery_level
  Integer 0 to 5
* accuracy
* correct_count
* wrong_count
* srs_stage
* last_seen
* last_reviewed
* next_review

## ReviewLog

Fields:

* id
* user_id
* learning_item_id
* review_type
* prompt
* user_answer
* correct_answer
* is_correct
* time_taken_seconds
* created_at

## MistakeLog

Fields:

* id
* user_id
* learning_item_id
* mistake_text
* correct_answer
* explanation
* resolved
* created_at

## StudySession

Fields:

* id
* user_id
* started_at
* ended_at
* xp_earned
* reviews_completed
* lessons_completed
* minutes_studied

Acceptance criteria:

* Models are connected correctly with relationships.
* Database can be created from scratch.
* Existing auth still works.
* Add comments where the model purpose is not obvious.

---

# Prompt 4 — Build seed data system

Create a seed data system for NihongoPath.

Requirements:

1. Add a CLI command or script called `seed.py`.
2. Seed all hiragana.
3. Seed all katakana.
4. Seed a small starter vocabulary set.
5. Seed a starter grammar set inspired by Tae Kim’s beginner order.

Do not copy long Tae Kim explanations. Use short original explanations and include source links.

Seed these grammar points:

* State of being
* Particle は
* Particle が
* Particle を
* Particle に
* Particle で
* Particle の
* い-adjectives
* な-adjectives
* ru-verbs
* u-verbs
* negative verbs
* past tense
* te-form
* polite form

For grammar items, include:

* title
* slug
* short explanation
* pattern
* example sentence
* source name: Tae Kim’s Guide to Japanese Grammar
* source URL placeholder or real URL field

Acceptance criteria:

* Running the seed script fills the database.
* Running it twice does not create duplicates.
* The app can display seeded items later.

---

# Prompt 5 — Design the dashboard page

Build the logged-in dashboard page.

The dashboard should show:

1. Daily progress card:

   * XP today
   * daily goal XP
   * reviews completed today
   * current streak

2. Recommended next study card:

   * If the user has due reviews, recommend reviews.
   * Otherwise recommend the next unseen learning item.

3. Skill progress cards:

   * Kana
   * Kanji
   * Vocabulary
   * Grammar
   * Reading
   * Listening
   * Writing

4. Due review queue:

   * Count of due items by type.

5. Recent mistakes:

   * Last 5 unresolved mistakes.

6. Continue learning button.

Visual style:

* dark cards
* pink/cyan/yellow accents
* rounded corners
* clean spacing
* gamified feel

Acceptance criteria:

* Dashboard uses real database data where possible.
* If the user has no progress, show useful empty states.
* The layout looks polished and responsive.

---

# Prompt 6 — Create the Study Path page

Build a `/study-path` page that shows a gamified progression map.

Requirements:

1. Group learning into worlds:

   * Kana Island
   * Basic Sentences
   * Particles
   * Adjectives
   * Verbs
   * Kanji Forest
   * Reading Village
   * Listening Harbor
   * Writing Dojo

2. Each world should show lesson nodes.

3. Nodes should have states:

   * locked
   * available
   * in progress
   * completed
   * mastered

4. Determine state from `UserProgress`.

5. Use a visually gamified layout with cards or connected nodes.

6. Clicking an available node opens the lesson page.

Acceptance criteria:

* The page displays seeded lessons grouped into worlds.
* Completed/mastered items visually differ from locked/unseen items.
* The layout works on desktop and mobile.

---

# Prompt 7 — Build generic lesson page

Create a reusable lesson page route:

`/learn/<slug>`

The page should support different learning item types.

For each lesson, show:

* title
* item type
* Japanese text
* reading
* meaning
* explanation
* examples if available
* source link if available
* related tags
* current mastery status
* buttons:

  * Mark as seen
  * Start quiz
  * Add to review
  * Mark as known

When the user clicks “Mark as seen”:

* Create or update UserProgress.
* Set status to `seen`.
* Set mastery_level to at least 1.
* Set next_review to now or soon.

When the user clicks “Mark as known”:

* Set status to `known`.
* Set mastery_level to at least 3.

Acceptance criteria:

* Any LearningItem can be viewed.
* Progress updates correctly.
* The user is redirected back with flash confirmation.
* The page is styled nicely.

---

# Prompt 8 — Build Kana module

Create `/kana`, `/kana/hiragana`, and `/kana/katakana`.

Requirements:

1. Show all hiragana and katakana in grid form.
2. Each kana card should show:

   * kana character
   * romaji
   * example word if available
   * user mastery status
3. Add filters:

   * all
   * unknown
   * learning
   * known
   * mastered
4. Add practice buttons:

   * Recognition practice
   * Typing practice
   * Audio placeholder practice

Create a kana quiz route:

`/practice/kana`

Quiz types:

* Show kana, user types romaji.
* Show romaji, user picks kana from choices.

On answer:

* Check correctness.
* Update UserProgress.
* Create ReviewLog.
* Add XP.
* If wrong, create MistakeLog.

Acceptance criteria:

* User can practice kana.
* Progress changes after answers.
* Wrong answers are logged.
* Correct answers increase mastery.

---

# Prompt 9 — Build Grammar module

Create `/grammar`.

Requirements:

1. List all grammar learning items.
2. Group grammar by beginner path order:

   * Basics
   * Particles
   * Adjectives
   * Verbs
   * Conjugation
   * Sentence patterns
3. Each grammar card shows:

   * title
   * short explanation
   * JLPT level if set
   * mastery status
   * source name
4. Clicking a grammar item opens the generic lesson page.
5. Add a grammar detail page design that is nicer than generic lessons if item_type is grammar.

Grammar detail page should show:

* explanation
* pattern
* example sentence
* common mistake section
* Tae Kim reference link
* mini practice section
* writing prompt section
* mastery status

Acceptance criteria:

* Grammar page is usable as a Tae Kim-inspired curriculum.
* Source is clearly shown.
* No long copied Tae Kim text is used.
* User can track grammar mastery.

---

# Prompt 10 — Add vocabulary module

Create `/vocabulary`.

Requirements:

1. List vocabulary items.
2. Add filters:

   * JLPT level
   * known status
   * tag/topic
3. Vocabulary cards show:

   * Japanese
   * reading
   * meaning
   * JLPT level
   * mastery status
4. Add vocabulary quiz:

   * Japanese → meaning
   * meaning → Japanese
   * reading recognition

On answer:

* Update progress.
* Log review.
* Add XP.
* Log mistakes.

Acceptance criteria:

* Vocabulary can be browsed.
* Vocabulary can be reviewed.
* Progress and mistakes are tracked.

---

# Prompt 11 — Add Kanji module

Create `/kanji`.

Requirements:

1. List kanji learning items.
2. Kanji cards show:

   * kanji
   * meaning
   * readings
   * JLPT level
   * mastery status
3. Add kanji detail page with:

   * kanji
   * readings
   * meanings
   * example words
   * related vocabulary
   * similar kanji warning placeholder
4. Add kanji quiz:

   * kanji → meaning
   * kanji → reading
   * meaning → kanji

Acceptance criteria:

* Kanji module works with existing LearningItem model.
* User progress is tracked.
* Wrong answers are logged.

---

# Prompt 12 — Build SRS review system

Implement a basic spaced repetition system.

Requirements:

1. Create a service called `srs_service.py`.
2. Implement review stages:

   * 0 new
   * 1 apprentice 1: 4 hours
   * 2 apprentice 2: 8 hours
   * 3 apprentice 3: 1 day
   * 4 guru: 3 days
   * 5 master: 7 days
   * 6 enlightened: 14 days
   * 7 burned: 30 days
3. If answer is correct:

   * increase correct_count
   * increase srs_stage
   * increase mastery_level if appropriate
   * schedule next_review
4. If answer is wrong:

   * increase wrong_count
   * lower srs_stage
   * set status to weak
   * schedule next_review sooner
   * create MistakeLog
5. Create `/reviews` page.
6. Show due reviews only.
7. Add mixed review mode.

Acceptance criteria:

* Due reviews are calculated correctly.
* Correct and wrong answers update SRS state.
* Review page can handle kana, vocabulary, kanji, and grammar items.
* Dashboard due review counts use this system.

---

# Prompt 13 — Build Progress page

Create a comprehensive `/progress` page.

Requirements:

1. Show overall stats:

   * total XP
   * level
   * streak
   * total reviews
   * total correct
   * total wrong
   * overall accuracy

2. Show known/mastered counts by item type:

   * kana
   * kanji
   * vocabulary
   * grammar
   * reading
   * listening
   * writing

3. Use Chart.js to show:

   * skill radar chart
   * review accuracy chart
   * progress by category bar chart

4. Show weak areas:

   * item types with low accuracy
   * recent mistakes
   * most failed items

5. Show JLPT readiness placeholder:

   * N5 readiness calculated from beginner item completion

Acceptance criteria:

* Progress page uses real user data.
* Charts render correctly.
* Empty states are handled cleanly.
* Page feels like a serious study tracker.

---

# Prompt 14 — Add Mistake Log and Notebook

Create `/notebook`.

Requirements:

1. Show unresolved mistakes.
2. Show resolved mistakes.
3. Let user mark mistakes as resolved.
4. Let user create personal notes.
5. Add a `UserNote` model:

   * id
   * user_id
   * title
   * body
   * related_learning_item_id
   * created_at
   * updated_at
6. Let users create, edit, and delete notes.
7. Allow notes to be linked to grammar/vocabulary/kanji items.

Acceptance criteria:

* Mistakes are visible and useful.
* Notes can be created and edited.
* Notebook feels like a personal Japanese study journal.

---

# Prompt 15 — Add Writing Practice module

Create `/writing`.

Requirements:

1. Create a `WritingPrompt` using LearningItem with item_type `writing_prompt`.
2. Show writing prompts such as:

   * Write “I am a student.”
   * Write “I drank water yesterday.”
   * Write “I study Japanese every day.”
3. User submits Japanese text.
4. Store writing attempts in a new model `WritingAttempt`:

   * id
   * user_id
   * prompt_id
   * user_text
   * feedback
   * created_at
5. For now, feedback can be rule-based/simple:

   * Check if answer is empty.
   * Check if expected keywords appear.
   * Show model answer.
6. Add XP for submitting.
7. Add mistake log if answer does not include expected keywords.

Acceptance criteria:

* User can write Japanese sentences.
* Attempts are saved.
* Writing history is shown.
* The system is ready for AI feedback later.

---

# Prompt 16 — Add Reading Practice module

Create `/reading`.

Requirements:

1. Add reading passages as LearningItem with item_type `reading`.
2. Create a `ReadingPassage` model if needed:

   * id
   * learning_item_id
   * japanese_text
   * furigana_text
   * english_translation
   * difficulty
   * grammar_tags
   * vocabulary_tags
3. Reading page should show:

   * Japanese text
   * toggle furigana
   * toggle translation
   * grammar used
   * vocabulary used
4. User can mark passage as:

   * read
   * understood
   * difficult
5. Add a short comprehension quiz.

Acceptance criteria:

* Reading passages display nicely.
* User can track reading progress.
* Reading practice contributes to progress stats.

---

# Prompt 17 — Add Listening Practice module

Create `/listening`.

Requirements:

1. Add listening items as LearningItem with item_type `listening`.
2. Create a `ListeningClip` model:

   * id
   * learning_item_id
   * audio_url
   * transcript_japanese
   * transcript_reading
   * translation
   * difficulty
3. For now, audio can use placeholder files or placeholder URLs.
4. Listening page should show:

   * audio player
   * hide/show transcript
   * hide/show translation
   * vocabulary list
   * grammar list
5. Add listening quiz:

   * multiple choice meaning
   * fill missing word
   * transcript reveal

Acceptance criteria:

* Listening page works even with placeholder audio.
* Listening progress is tracked.
* User can review listening items through SRS later.

---

# Prompt 18 — Add conjugation practice

Create `/conjugation`.

Requirements:

1. Add a conjugation practice system for verbs.
2. Start with these forms:

   * dictionary
   * polite present
   * polite past
   * negative
   * past negative
   * te-form
3. Create a small verb dataset:

   * 食べる
   * 見る
   * 行く
   * 飲む
   * する
   * 来る
4. Show prompt like:

   * 食べる → polite past
5. User types answer.
6. System checks against expected answer.
7. Log review and mistakes.
8. Track conjugation as its own skill on the progress page.

Acceptance criteria:

* Conjugation practice works.
* Correct answers are checked.
* Mistakes are logged.
* Progress page includes conjugation stats.

---

# Prompt 19 — Add smart recommendations

Create a recommendation service.

File:

`app/services/recommendation_service.py`

Requirements:

Recommend what the user should study next using this priority:

1. Due reviews first.
2. Weak items second.
3. Unresolved mistakes third.
4. Next unseen item in study path fourth.
5. Random low-mastery item fifth.

Dashboard should show:

* recommended item title
* reason
* button to start

Example reasons:

* “You have 24 due reviews.”
* “You often miss particle が.”
* “You have unresolved mistakes.”
* “This is the next lesson in your study path.”

Acceptance criteria:

* Recommendations are generated from real user data.
* Dashboard displays one main recommendation.
* Recommendations are never empty unless database has no content.

---

# Prompt 20 — Polish UI style

Improve the whole UI style.

Requirements:

1. Make the website visually consistent.
2. Use dark theme:

   * background `#0B1020`
   * card background `#141A2E`
   * pink accent `#FF5C8A`
   * cyan accent `#35D0FF`
   * yellow accent `#FFD166`
3. Use rounded cards, soft shadows, hover effects.
4. Add Japanese visual details:

   * small kana/kanji background decorations
   * progress badges
   * XP pill
   * level badge
5. Improve mobile responsiveness.
6. Improve buttons, forms, tables, and cards.
7. Add empty-state illustrations using simple emoji/icons if needed.

Acceptance criteria:

* Website looks like a polished Japanese study dashboard.
* All pages share the same visual language.
* Mobile layout is usable.
* No page looks like plain Bootstrap/default HTML.

---

# Prompt 21 — Add admin/content management

Create a simple admin panel for adding/editing learning content.

Routes:

* `/admin`
* `/admin/items`
* `/admin/items/new`
* `/admin/items/<id>/edit`
* `/admin/items/<id>/delete`

Requirements:

1. Add `is_admin` boolean to User model.
2. Only admins can access admin pages.
3. Admin can create/edit/delete LearningItems.
4. Admin form should support:

   * type
   * title
   * slug
   * Japanese
   * reading
   * meaning
   * explanation
   * JLPT level
   * difficulty
   * source name
   * source URL
   * tags
5. Add search/filter in admin item list.

Acceptance criteria:

* Admin can manage content.
* Non-admin users cannot access admin.
* Existing seed data can be edited through admin panel.

---

# Prompt 22 — Add onboarding and placement

Create onboarding for new users.

Routes:

* `/onboarding`
* `/onboarding/goal`
* `/onboarding/level`
* `/onboarding/complete`

Requirements:

1. Ask the user’s goal:

   * JLPT N5
   * Travel
   * Anime/listening
   * Reading manga
   * School
   * General learning
2. Ask current level:

   * Complete beginner
   * Know kana
   * Know some grammar
   * Intermediate
3. Store onboarding answers in User model:

   * study_goal
   * starting_level
   * onboarding_complete
4. After onboarding, redirect to dashboard.
5. Dashboard recommendations should consider goal and level.

Acceptance criteria:

* New users go through onboarding.
* Existing users are not forced through it again.
* Dashboard adapts slightly to user goal.

---

# Prompt 23 — Add tests

Add basic automated tests.

Use pytest.

Test:

1. App starts.
2. User can register.
3. User can log in.
4. Dashboard requires login.
5. Seed data creates kana and grammar.
6. UserProgress updates when marking lesson as seen.
7. SRS stage changes after correct answer.
8. MistakeLog is created after wrong answer.
9. Admin pages reject non-admins.

Acceptance criteria:

* Tests can be run with `pytest`.
* Tests use a temporary test database.
* Existing app still works normally.

---

# Prompt 24 — Add README and developer documentation

Improve documentation.

Add:

1. README with:

   * project description
   * screenshots placeholder
   * setup instructions
   * database setup
   * seeding
   * running tests
   * project structure
   * main features
2. Add `docs/content-model.md`.
3. Add `docs/srs-system.md`.
4. Add `docs/grammar-source-policy.md`.

In `grammar-source-policy.md`, explain:

* Grammar curriculum is inspired by Tae Kim.
* Do not copy large lesson text.
* Use original explanations.
* Link to original Tae Kim pages.
* Create original examples and exercises.

Acceptance criteria:

* A new developer can understand and run the project.
* Content copyright approach is documented.
* SRS logic is documented.

---

# Prompt 25 — Final integration pass

Do a final integration and bug-fix pass over the whole NihongoPath project.

Tasks:

1. Run the app.
2. Check all major routes:

   * landing
   * dashboard
   * study path
   * kana
   * grammar
   * vocabulary
   * kanji
   * reviews
   * progress
   * notebook
   * writing
   * reading
   * listening
   * conjugation
   * admin
3. Fix broken links.
4. Fix template errors.
5. Fix database relationship issues.
6. Fix styling inconsistencies.
7. Ensure empty states exist.
8. Ensure logged-out users are redirected properly.
9. Ensure seeded data works.
10. Run tests and fix failures.

Acceptance criteria:

* App runs from fresh clone.
* Database can be initialized and seeded.
* User can register, log in, study, review, and see progress.
* No obvious broken pages.
* Tests pass.
