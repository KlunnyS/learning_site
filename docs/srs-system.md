# SRS System

SRS logic lives in `app/services/srs_service.py`.

Stages:

- 0 new: 10 minutes
- 1 apprentice 1: 4 hours
- 2 apprentice 2: 8 hours
- 3 apprentice 3: 1 day
- 4 guru: 3 days
- 5 master: 7 days
- 6 enlightened: 14 days
- 7 burned: 30 days

Correct answers increase `correct_count`, move the item up one stage, update mastery, schedule the next review, log a `ReviewLog`, and award XP.

Wrong answers increase `wrong_count`, lower the stage, mark the item weak, schedule a short retry, log a `ReviewLog`, and create a `MistakeLog`.
