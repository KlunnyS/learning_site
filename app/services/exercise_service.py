import random

from app.models import LearningItem, UserProgress, utcnow


def answer_for(item):
    if item.item_type == "kana":
        return item.reading or item.meaning or item.title
    if item.item_type in {"vocabulary", "kanji"}:
        return item.meaning or item.reading or item.japanese
    if item.item_type == "conjugation":
        return item.meaning
    if item.item_type == "grammar":
        return item.pattern or item.meaning or item.title
    return item.meaning or item.reading or item.title


def prompt_for(item):
    if item.item_type == "grammar":
        return item.example_sentence or item.pattern or item.title
    if item.item_type == "conjugation":
        return item.title
    return item.japanese or item.title


def instruction_for(item):
    instructions = {
        "kana": "Type the romaji reading.",
        "vocabulary": "Type the English meaning.",
        "kanji": "Type the core meaning.",
        "grammar": "Type the grammar pattern.",
        "conjugation": "Type the requested conjugated form.",
        "reading": "Type the English meaning.",
        "listening": "Type the English meaning.",
    }
    return instructions.get(item.item_type, "Type the answer.")


def exercise_type_for(item):
    if item.item_type == "grammar":
        return "pattern"
    if item.item_type == "conjugation":
        return "production"
    if item.item_type in {"kana", "vocabulary", "kanji"}:
        return "recall"
    return "comprehension"


def is_due(next_review):
    if not next_review:
        return False
    now = utcnow()
    if next_review.tzinfo is None:
        now = now.replace(tzinfo=None)
    return next_review <= now


def score_item(item, progress):
    if not progress:
        return 40 - (item.difficulty or 1)
    score = 0
    if progress.status == "weak":
        score += 100
    if is_due(progress.next_review):
        score += 80
    score += max(0, 5 - (progress.mastery_level or 0)) * 10
    score += max(0, 100 - (progress.accuracy or 0)) / 5
    return score


def select_adaptive_item(user, items):
    if not items:
        return None
    progress_rows = UserProgress.query.filter(
        UserProgress.user_id == user.id,
        UserProgress.learning_item_id.in_([item.id for item in items]),
    ).all()
    progress_by_item = {progress.learning_item_id: progress for progress in progress_rows}
    ranked = sorted(items, key=lambda item: score_item(item, progress_by_item.get(item.id)), reverse=True)
    highest_score = score_item(ranked[0], progress_by_item.get(ranked[0].id))
    strongest = [item for item in ranked if score_item(item, progress_by_item.get(item.id)) == highest_score]
    return random.choice(strongest)


def build_exercise(item, pool=None):
    if not item:
        return None
    pool = pool or [item]
    answer = answer_for(item)
    choices = []
    if item.item_type in {"kana", "vocabulary", "kanji", "grammar"}:
        seen = set()
        for candidate in random.sample(pool, min(len(pool), 6)):
            candidate_answer = answer_for(candidate)
            if candidate_answer and candidate_answer not in seen:
                seen.add(candidate_answer)
                choices.append(candidate_answer)
        if answer and answer not in seen:
            choices = ([answer] + choices)[:4]
        else:
            choices = choices[:4]
        random.shuffle(choices)
    return {
        "item": item,
        "type": exercise_type_for(item),
        "prompt": prompt_for(item),
        "instruction": instruction_for(item),
        "answer": answer,
        "choices": choices,
    }


def check_answer(item, answer):
    expected = answer_for(item) or ""
    return answer.strip().lower() == expected.strip().lower()
