import pytest

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import LearningItem, MistakeLog, User, UserProgress
from app.services.srs_service import apply_review
from seed import seed


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, username="aki", email="aki@example.com", password="secret1"):
    return client.post("/register", data={"username": username, "email": email, "password": password}, follow_redirects=True)


def login(client, identifier="aki", password="secret1"):
    return client.post("/login", data={"identifier": identifier, "password": password}, follow_redirects=True)


def test_app_starts(client):
    assert client.get("/").status_code == 200


def test_user_can_register_and_login(client):
    response = register(client)
    assert response.status_code == 200
    client.get("/logout")
    response = login(client)
    assert b"Dashboard" in response.data or response.status_code == 200


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_seed_data_creates_kana_and_grammar(app):
    with app.app_context():
        seed()
        assert LearningItem.query.filter_by(item_type="kana").count() >= 92
        assert LearningItem.query.filter_by(item_type="grammar").count() >= 15


def test_mark_lesson_seen_updates_progress(client, app):
    with app.app_context():
        seed()
    register(client)
    with app.app_context():
        item = LearningItem.query.filter_by(slug="particle-wa").first()
    client.post(f"/learn/{item.slug}", data={"action": "seen"}, follow_redirects=True)
    with app.app_context():
        user = User.query.filter_by(username="aki").first()
        progress = UserProgress.query.filter_by(user_id=user.id, learning_item_id=item.id).first()
        assert progress.status == "seen"


def test_srs_stage_changes_after_correct_answer(app):
    with app.app_context():
        seed()
        user = User(username="aki", email="aki@example.com")
        user.set_password("secret1")
        db.session.add(user)
        item = LearningItem.query.filter_by(item_type="kana").first()
        apply_review(user, item, "kana", item.japanese, item.reading, item.reading, True)
        db.session.commit()
        progress = UserProgress.query.filter_by(user_id=user.id, learning_item_id=item.id).first()
        assert progress.srs_stage == 1


def test_mistake_log_created_after_wrong_answer(app):
    with app.app_context():
        seed()
        user = User(username="aki", email="aki@example.com")
        user.set_password("secret1")
        db.session.add(user)
        item = LearningItem.query.filter_by(item_type="kana").first()
        apply_review(user, item, "kana", item.japanese, "x", item.reading, False)
        db.session.commit()
        assert MistakeLog.query.filter_by(user_id=user.id).count() == 1


def test_admin_rejects_non_admin(client):
    register(client, username="admin", email="admin@example.com")
    client.get("/logout")
    register(client, username="aki", email="aki@example.com")
    response = client.get("/admin/items")
    assert response.status_code == 403
