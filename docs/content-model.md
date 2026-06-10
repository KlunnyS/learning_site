# Content Model

NihongoPath centers content around `LearningItem`.

`LearningItem.item_type` separates kana, kanji, vocabulary, grammar, reading, listening, writing prompts, and conjugation prompts. Shared fields such as `japanese`, `reading`, `meaning`, `explanation`, `tags`, and source metadata allow the same lesson and progress routes to work across content types.

User-specific state is stored in `UserProgress`, keyed by user and learning item. Reviews are append-only `ReviewLog` rows. Errors are stored in `MistakeLog` until the learner resolves them. Personal study notes live in `UserNote`.

Specialized practice models extend the shared item:

- `ReadingPassage` adds furigana, translation, grammar tags, and vocabulary tags.
- `ListeningClip` adds audio URL, transcript, reading, and translation.
- `WritingAttempt` stores submitted writing and simple feedback.
