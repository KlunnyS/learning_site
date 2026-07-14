from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    xp = db.Column(db.Integer, default=0, nullable=False)
    level = db.Column(db.Integer, default=1, nullable=False)
    streak = db.Column(db.Integer, default=0, nullable=False)
    daily_goal_xp = db.Column(db.Integer, default=50, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    study_goal = db.Column(db.String(80))
    starting_level = db.Column(db.String(80))
    onboarding_complete = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    progress = db.relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    reviews = db.relationship("ReviewLog", back_populates="user", cascade="all, delete-orphan")
    mistakes = db.relationship("MistakeLog", back_populates="user", cascade="all, delete-orphan")
    notes = db.relationship("UserNote", back_populates="user", cascade="all, delete-orphan")
    lesson_progress = db.relationship("LessonProgress", back_populates="user", cascade="all, delete-orphan")
    daily_activity = db.relationship("DailyActivity", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = db.relationship("LessonQuizAttempt", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_xp(self, amount):
        self.xp += amount
        self.level = max(1, self.xp // 100 + 1)


class LearningItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(40), nullable=False, index=True)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    japanese = db.Column(db.Text)
    reading = db.Column(db.String(255))
    meaning = db.Column(db.String(255))
    explanation = db.Column(db.Text)
    pattern = db.Column(db.String(255))
    example_sentence = db.Column(db.Text)
    jlpt_level = db.Column(db.String(10))
    difficulty = db.Column(db.Integer, default=1)
    source_name = db.Column(db.String(255))
    source_url = db.Column(db.String(500))
    tags = db.Column(db.String(500))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    progress = db.relationship("UserProgress", back_populates="learning_item", cascade="all, delete-orphan")
    reviews = db.relationship("ReviewLog", back_populates="learning_item", cascade="all, delete-orphan")
    mistakes = db.relationship("MistakeLog", back_populates="learning_item", cascade="all, delete-orphan")
    lesson_links = db.relationship("LessonItem", back_populates="learning_item", cascade="all, delete-orphan")
    examples = db.relationship("ExampleSentence", back_populates="learning_item", cascade="all, delete-orphan")


class ExampleSentence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    learning_item_id = db.Column(db.Integer, db.ForeignKey("learning_item.id"), nullable=False, index=True)
    japanese = db.Column(db.Text, nullable=False)
    reading = db.Column(db.Text)
    english = db.Column(db.Text, nullable=False)
    note = db.Column(db.Text)
    difficulty = db.Column(db.Integer, default=1, nullable=False)
    source_name = db.Column(db.String(255))
    source_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    learning_item = db.relationship("LearningItem", back_populates="examples")


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.String(40), default="N5", nullable=False)
    skill_focus = db.Column(db.String(80), nullable=False, index=True)
    sequence = db.Column(db.Integer, default=0, nullable=False, index=True)
    xp_reward = db.Column(db.Integer, default=20, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    items = db.relationship("LessonItem", back_populates="lesson", cascade="all, delete-orphan", order_by="LessonItem.position")
    progress = db.relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    quiz_attempts = db.relationship("LessonQuizAttempt", back_populates="lesson", cascade="all, delete-orphan")


class LessonItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, index=True)
    learning_item_id = db.Column(db.Integer, db.ForeignKey("learning_item.id"), nullable=False, index=True)
    position = db.Column(db.Integer, default=0, nullable=False)
    role = db.Column(db.String(40), default="core", nullable=False)

    lesson = db.relationship("Lesson", back_populates="items")
    learning_item = db.relationship("LearningItem", back_populates="lesson_links")
    __table_args__ = (db.UniqueConstraint("lesson_id", "learning_item_id", name="uq_lesson_learning_item"),)


class LessonProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, index=True)
    status = db.Column(db.String(30), default="not_started", nullable=False)
    items_seen = db.Column(db.Integer, default=0, nullable=False)
    exercises_correct = db.Column(db.Integer, default=0, nullable=False)
    exercises_attempted = db.Column(db.Integer, default=0, nullable=False)
    started_at = db.Column(db.DateTime(timezone=True))
    completed_at = db.Column(db.DateTime(timezone=True))
    last_activity = db.Column(db.DateTime(timezone=True))

    user = db.relationship("User", back_populates="lesson_progress")
    lesson = db.relationship("Lesson", back_populates="progress")
    __table_args__ = (db.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),)

    @property
    def accuracy(self):
        if not self.exercises_attempted:
            return 0.0
        return round((self.exercises_correct / self.exercises_attempted) * 100, 1)


class LessonQuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, index=True)
    correct_count = db.Column(db.Integer, default=0, nullable=False)
    question_count = db.Column(db.Integer, default=0, nullable=False)
    score_percent = db.Column(db.Float, default=0.0, nullable=False)
    passed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    user = db.relationship("User", back_populates="quiz_attempts")
    lesson = db.relationship("Lesson", back_populates="quiz_attempts")


class UserProgress(db.Model):
    # Per-user mastery and SRS state for one learning item.
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    learning_item_id = db.Column(db.Integer, db.ForeignKey("learning_item.id"), nullable=False, index=True)
    status = db.Column(db.String(30), default="unknown", nullable=False)
    mastery_level = db.Column(db.Integer, default=0, nullable=False)
    accuracy = db.Column(db.Float, default=0.0, nullable=False)
    correct_count = db.Column(db.Integer, default=0, nullable=False)
    wrong_count = db.Column(db.Integer, default=0, nullable=False)
    srs_stage = db.Column(db.Integer, default=0, nullable=False)
    last_seen = db.Column(db.DateTime(timezone=True))
    last_reviewed = db.Column(db.DateTime(timezone=True))
    next_review = db.Column(db.DateTime(timezone=True))

    user = db.relationship("User", back_populates="progress")
    learning_item = db.relationship("LearningItem", back_populates="progress")
    __table_args__ = (db.UniqueConstraint("user_id", "learning_item_id", name="uq_user_item_progress"),)

    def recalculate_accuracy(self):
        total = self.correct_count + self.wrong_count
        self.accuracy = round((self.correct_count / total) * 100, 1) if total else 0.0


class ReviewLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    learning_item_id = db.Column(db.Integer, db.ForeignKey("learning_item.id"), nullable=False, index=True)
    review_type = db.Column(db.String(50), nullable=False)
    prompt = db.Column(db.Text)
    user_answer = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    time_taken_seconds = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    user = db.relationship("User", back_populates="reviews")
    learning_item = db.relationship("LearningItem", back_populates="reviews")


class DailyActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    activity_date = db.Column(db.Date, nullable=False, index=True)
    xp_earned = db.Column(db.Integer, default=0, nullable=False)
    reviews_completed = db.Column(db.Integer, default=0, nullable=False)
    lessons_completed = db.Column(db.Integer, default=0, nullable=False)
    correct_reviews = db.Column(db.Integer, default=0, nullable=False)
    wrong_reviews = db.Column(db.Integer, default=0, nullable=False)
    last_activity_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="daily_activity")
    __table_args__ = (db.UniqueConstraint("user_id", "activity_date", name="uq_user_daily_activity"),)


class MistakeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    learning_item_id = db.Column(db.Integer, db.ForeignKey("learning_item.id"), nullable=True, index=True)
    mistake_text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text)
    explanation = db.Column(db.Text)
    resolved = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="mistakes")
    learning_item = db.relationship("LearningItem", back_populates="mistakes")


class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    started_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    ended_at = db.Column(db.DateTime(timezone=True))
    xp_earned = db.Column(db.Integer, default=0, nullable=False)
    reviews_completed = db.Column(db.Integer, default=0, nullable=False)
    lessons_completed = db.Column(db.Integer, default=0, nullable=False)
    minutes_studied = db.Column(db.Integer, default=0, nullable=False)


class UserNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    related_learning_item_id = db.Column(db.Integer, db.ForeignKey("learning_item.id"))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = db.relationship("User", back_populates="notes")
    related_learning_item = db.relationship("LearningItem")


class WritingAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey("learning_item.id"), nullable=False)
    user_text = db.Column(db.Text, nullable=False)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    prompt = db.relationship("LearningItem")


class ReadingPassage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    learning_item_id = db.Column(db.Integer, db.ForeignKey("learning_item.id"), nullable=False, unique=True)
    japanese_text = db.Column(db.Text, nullable=False)
    furigana_text = db.Column(db.Text)
    english_translation = db.Column(db.Text)
    difficulty = db.Column(db.Integer, default=1)
    grammar_tags = db.Column(db.String(500))
    vocabulary_tags = db.Column(db.String(500))

    learning_item = db.relationship("LearningItem")


class ListeningClip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    learning_item_id = db.Column(db.Integer, db.ForeignKey("learning_item.id"), nullable=False, unique=True)
    audio_url = db.Column(db.String(500))
    transcript_japanese = db.Column(db.Text)
    transcript_reading = db.Column(db.Text)
    translation = db.Column(db.Text)
    difficulty = db.Column(db.Integer, default=1)

    learning_item = db.relationship("LearningItem")
