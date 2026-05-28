import pytest
from app import app as flask_app, db as _db
from models import User, Schedule
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta


@pytest.fixture()
def app():
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    flask_app.config["WTF_CSRF_ENABLED"] = False
    flask_app.config["SECRET_KEY"] = "test-secret-key"

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def _csrf(client):
    """Set a fixed CSRF token in the session."""
    with client.session_transaction() as sess:
        sess["csrf_token"] = "test-csrf"
    return "test-csrf"


@pytest.fixture()
def form(_csrf):
    """Return a helper to build form data with CSRF token."""
    def _form(**kwargs):
        d = {"csrf_token": _csrf}
        d.update(kwargs)
        return d
    return _form


@pytest.fixture()
def admin(app):
    with app.app_context():
        u = User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            is_admin=True,
            real_name="管理员",
        )
        _db.session.add(u)
        _db.session.commit()
        return u.id


@pytest.fixture()
def user(app):
    with app.app_context():
        u = User(
            username="testuser",
            password_hash=generate_password_hash("123456"),
            real_name="测试用户",
            phone="13800000000",
        )
        _db.session.add(u)
        _db.session.commit()
        return u.id


@pytest.fixture()
def user2(app):
    with app.app_context():
        u = User(
            username="testuser2",
            password_hash=generate_password_hash("123456"),
            real_name="测试用户2",
            phone="13800000001",
        )
        _db.session.add(u)
        _db.session.commit()
        return u.id


@pytest.fixture()
def schedule(app):
    with app.app_context():
        s = Schedule(
            departure="北京",
            destination="上海",
            departure_time=datetime.now() + timedelta(days=1, hours=8),
            arrival_time=datetime.now() + timedelta(days=1, hours=14),
            price=150.0,
            total_seats=5,
            available_seats=5,
        )
        _db.session.add(s)
        _db.session.commit()
        return s.id


@pytest.fixture()
def full_schedule(app):
    with app.app_context():
        s = Schedule(
            departure="北京",
            destination="广州",
            departure_time=datetime.now() + timedelta(days=1, hours=8),
            arrival_time=datetime.now() + timedelta(days=1, hours=16),
            price=200.0,
            total_seats=2,
            available_seats=0,
        )
        _db.session.add(s)
        _db.session.commit()
        return s.id


@pytest.fixture()
def login(client):
    """Return a helper to log in as a given user."""
    def _login(username, password="123456"):
        with client.session_transaction() as sess:
            sess["csrf_token"] = "test-csrf"
        return client.post("/login", data={
            "username": username,
            "password": password,
            "csrf_token": "test-csrf",
        }, follow_redirects=True)
    return _login
