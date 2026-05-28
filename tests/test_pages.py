"""Tests for public pages, search, schedule detail, favorites."""
from app import db
from models import Schedule, Favorite
from datetime import datetime, timedelta


class TestPublicPages:
    def test_index(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "汽车订票平台".encode() in r.data

    def test_search_page(self, client):
        r = client.get("/search")
        assert r.status_code == 200

    def test_search_by_departure(self, app, client):
        with app.app_context():
            db.session.add(Schedule(
                departure="北京", destination="上海",
                departure_time=datetime.now() + timedelta(days=1),
                arrival_time=datetime.now() + timedelta(days=1, hours=5),
                price=100, total_seats=40, available_seats=40,
            ))
            db.session.add(Schedule(
                departure="广州", destination="深圳",
                departure_time=datetime.now() + timedelta(days=1),
                arrival_time=datetime.now() + timedelta(days=1, hours=2),
                price=80, total_seats=40, available_seats=40,
            ))
            db.session.commit()
        r = client.get("/search?departure=北京")
        assert r.status_code == 200
        assert "北京".encode() in r.data

    def test_search_sort_price_asc(self, app, client):
        with app.app_context():
            db.session.add(Schedule(
                departure="A", destination="B",
                departure_time=datetime.now() + timedelta(days=1),
                arrival_time=datetime.now() + timedelta(days=1, hours=5),
                price=200, total_seats=40, available_seats=40,
            ))
            db.session.add(Schedule(
                departure="C", destination="D",
                departure_time=datetime.now() + timedelta(days=1),
                arrival_time=datetime.now() + timedelta(days=1, hours=2),
                price=50, total_seats=40, available_seats=40,
            ))
            db.session.commit()
        r = client.get("/search?sort=price_asc")
        assert r.status_code == 200
        html = r.data.decode()
        pos_cheap = html.find("50")
        pos_expensive = html.find("200")
        assert pos_cheap < pos_expensive

    def test_search_sort_duration_asc(self, app, client):
        with app.app_context():
            db.session.add(Schedule(
                departure="A", destination="B",
                departure_time=datetime.now() + timedelta(days=1),
                arrival_time=datetime.now() + timedelta(days=1, hours=8),
                price=100, total_seats=40, available_seats=40,
            ))
            db.session.add(Schedule(
                departure="C", destination="D",
                departure_time=datetime.now() + timedelta(days=1),
                arrival_time=datetime.now() + timedelta(days=1, hours=2),
                price=100, total_seats=40, available_seats=40,
            ))
            db.session.commit()
        r = client.get("/search?sort=duration_asc")
        assert r.status_code == 200


class TestScheduleDetail:
    def test_schedule_detail(self, client, schedule):
        r = client.get(f"/schedule/{schedule}")
        assert r.status_code == 200
        assert "北京".encode() in r.data
        assert "立即订票".encode() in r.data

    def test_schedule_detail_not_found(self, client):
        r = client.get("/schedule/99999")
        assert r.status_code == 404

    def test_cancelled_schedule_shows_cancelled(self, app, client):
        with app.app_context():
            s = Schedule(
                departure="X", destination="Y",
                departure_time=datetime.now() + timedelta(days=1),
                arrival_time=datetime.now() + timedelta(days=1, hours=3),
                price=100, total_seats=5, available_seats=0,
                status="cancelled",
            )
            db.session.add(s)
            db.session.commit()
            sid = s.id
        r = client.get(f"/schedule/{sid}")
        assert "班次已取消".encode() in r.data
        assert "已售罄".encode() not in r.data

    def test_sold_out_schedule_shows_waitlist_for_logged_in(self, app, client, login, user, full_schedule):
        login("testuser")
        r = client.get(f"/schedule/{full_schedule}")
        assert "候补订票".encode() in r.data


class TestFavorites:
    def test_favorite_requires_login(self, client, _csrf, schedule):
        r = client.post(f"/schedule/{schedule}/favorite", data={"csrf_token": _csrf},
                        follow_redirects=False)
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]

    def test_add_favorite(self, app, client, form, login, user, schedule):
        login("testuser")
        r = client.post(f"/schedule/{schedule}/favorite", data=form(),
                        follow_redirects=True)
        assert "已收藏".encode() in r.data
        with app.app_context():
            assert Favorite.query.filter_by(user_id=user, schedule_id=schedule).count() == 1

    def test_remove_favorite(self, app, client, form, login, user, schedule):
        login("testuser")
        client.post(f"/schedule/{schedule}/favorite", data=form())
        r = client.post(f"/schedule/{schedule}/favorite", data=form(),
                        follow_redirects=True)
        assert "已取消收藏".encode() in r.data
        with app.app_context():
            assert Favorite.query.filter_by(user_id=user, schedule_id=schedule).count() == 0

    def test_my_favorites_page(self, client, form, login, user, schedule):
        login("testuser")
        client.post(f"/schedule/{schedule}/favorite", data=form())
        r = client.get("/favorites")
        assert r.status_code == 200
        assert "我的收藏".encode() in r.data


class TestProfile:
    def test_profile_page(self, client, login, user):
        login("testuser")
        r = client.get("/profile")
        assert r.status_code == 200

    def test_update_profile(self, client, form, login, user):
        login("testuser")
        r = client.post("/profile", data=form(
            real_name="新名字", phone="13900000000", email="test@test.com",
        ), follow_redirects=True)
        assert "个人资料已更新".encode() in r.data


class TestAPI:
    def test_api_schedules(self, app, client, schedule):
        r = client.get("/api/schedules")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["departure"] == "北京"

    def test_403_page(self, client, login, user):
        login("testuser")
        r = client.get("/admin")
        assert r.status_code == 403

    def test_404_page(self, client):
        r = client.get("/nonexistent-page")
        assert r.status_code == 404
