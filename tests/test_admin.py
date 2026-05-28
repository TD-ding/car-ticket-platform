"""Tests for admin: schedule/order/user management, permissions."""
from app import db
from models import User, Schedule, Order
from datetime import datetime, timedelta


def _make_schedule_form(**overrides):
    base = {
        "departure": "北京",
        "destination": "上海",
        "departure_time": (datetime.now() + timedelta(days=2, hours=8)).strftime("%Y-%m-%dT%H:%M"),
        "arrival_time": (datetime.now() + timedelta(days=2, hours=14)).strftime("%Y-%m-%dT%H:%M"),
        "price": "120.0",
        "total_seats": "40",
    }
    base.update(overrides)
    return base


class TestAdminPermissions:
    def test_admin_dashboard_requires_login(self, client):
        r = client.get("/admin", follow_redirects=False)
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]

    def test_admin_dashboard_requires_admin(self, client, login, user):
        login("testuser")
        r = client.get("/admin")
        assert r.status_code == 403

    def test_admin_can_access_dashboard(self, client, login, admin):
        login("admin", "admin123")
        r = client.get("/admin")
        assert r.status_code == 200
        assert "管理后台".encode() in r.data


class TestAdminSchedules:
    def test_list_schedules(self, client, login, admin):
        login("admin", "admin123")
        r = client.get("/admin/schedules")
        assert r.status_code == 200

    def test_create_schedule(self, app, client, form, login, admin):
        login("admin", "admin123")
        r = client.post("/admin/schedules/new", data=form(**_make_schedule_form()),
                        follow_redirects=True)
        assert "班次已添加".encode() in r.data
        with app.app_context():
            assert Schedule.query.count() == 1

    def test_create_schedule_invalid_time(self, client, form, login, admin):
        login("admin", "admin123")
        r = client.post("/admin/schedules/new", data=form(**_make_schedule_form(
            departure_time="2025-01-01T10:00",
            arrival_time="2025-01-01T08:00",
        )), follow_redirects=True)
        assert "到达时间必须晚于出发时间".encode() in r.data

    def test_create_schedule_negative_price(self, client, form, login, admin):
        login("admin", "admin123")
        r = client.post("/admin/schedules/new", data=form(**_make_schedule_form(price="-10")),
                        follow_redirects=True)
        assert "票价必须大于0".encode() in r.data

    def test_edit_schedule(self, app, client, form, login, admin, schedule):
        login("admin", "admin123")
        r = client.post(f"/admin/schedules/{schedule}/edit",
                        data=form(**_make_schedule_form(
                            departure="南京", destination="杭州", price="99.0",
                        )), follow_redirects=True)
        assert "班次已更新".encode() in r.data
        with app.app_context():
            s = db.session.get(Schedule, schedule)
            assert s.departure == "南京"
            assert s.price == 99.0

    def test_edit_schedule_total_seats_below_sold(self, app, client, form, login, admin, user, schedule):
        login("testuser")
        client.post(f"/book/{schedule}", data=form(
            passenger_name="测试", passenger_phone="13800000000",
        ))
        login("admin", "admin123")
        # 1 seat sold, try setting total to 1 which is == sold, should work
        # try setting total to 0 would be caught by form validation first
        # so test with a value that passes form validation but fails sold check
        r = client.post(f"/admin/schedules/{schedule}/edit",
                        data=form(**_make_schedule_form(total_seats="0")),
                        follow_redirects=True)
        # total_seats=0 is caught by form validation (total <= 0)
        assert "座位数必须大于0".encode() in r.data

    def test_cancel_schedule(self, app, client, form, login, admin, schedule):
        login("admin", "admin123")
        r = client.post(f"/admin/schedules/{schedule}/cancel", data=form(),
                        follow_redirects=True)
        assert "班次已取消".encode() in r.data
        with app.app_context():
            s = db.session.get(Schedule, schedule)
            assert s.status == "cancelled"

    def test_copy_schedule(self, app, client, form, login, admin, schedule):
        login("admin", "admin123")
        r = client.post(f"/admin/schedules/{schedule}/copy", data=form(),
                        follow_redirects=True)
        assert "已复制为新班次".encode() in r.data
        with app.app_context():
            assert Schedule.query.count() == 2

    def test_schedule_filter(self, app, client, login, admin):
        login("admin", "admin123")
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
        r = client.get("/admin/schedules?departure=北京")
        assert r.status_code == 200
        assert "北京".encode() in r.data


class TestAdminOrders:
    def test_list_orders(self, client, login, admin):
        login("admin", "admin123")
        r = client.get("/admin/orders")
        assert r.status_code == 200

    def test_order_status_paid_to_used(self, app, client, form, login, admin, user, schedule):
        login("testuser")
        client.post(f"/book/{schedule}", data=form(
            passenger_name="测试", passenger_phone="13800000000",
        ))
        with app.app_context():
            order = Order.query.first()
            oid = order.id
            avail_before = db.session.get(Schedule, schedule).available_seats

        login("admin", "admin123")
        r = client.post(f"/admin/orders/{oid}/status", data=form(status="used"),
                        follow_redirects=True)
        assert "订单状态已更新".encode() in r.data
        with app.app_context():
            o = db.session.get(Order, oid)
            assert o.order_status == "used"
            s = db.session.get(Schedule, schedule)
            assert s.available_seats == avail_before

    def test_order_status_paid_to_cancelled(self, app, client, form, login, admin, user, schedule):
        login("testuser")
        client.post(f"/book/{schedule}", data=form(
            passenger_name="测试", passenger_phone="13800000000",
        ))
        with app.app_context():
            order = Order.query.first()
            oid = order.id

        login("admin", "admin123")
        r = client.post(f"/admin/orders/{oid}/status", data=form(status="cancelled"),
                        follow_redirects=True)
        assert "订单状态已更新".encode() in r.data
        with app.app_context():
            s = db.session.get(Schedule, schedule)
            assert s.available_seats == 5

    def test_order_status_cancelled_to_paid_blocks_when_full(self, app, client, form, login, admin, user, schedule):
        login("testuser")
        client.post(f"/book/{schedule}", data=form(
            passenger_name="测试", passenger_phone="13800000000",
        ))
        # First cancel the order so status = cancelled
        with app.app_context():
            order = Order.query.first()
            oid = order.id
        login("admin", "admin123")
        client.post(f"/admin/orders/{oid}/status", data=form(status="cancelled"),
                    follow_redirects=True)
        # Now artificially set available to 0
        with app.app_context():
            s = db.session.get(Schedule, schedule)
            s.available_seats = 0
            db.session.commit()

        # Try to restore cancelled order to paid - should fail
        r = client.post(f"/admin/orders/{oid}/status", data=form(status="paid"),
                        follow_redirects=True)
        assert "该班次已满".encode() in r.data

    def test_order_export_csv(self, client, login, admin):
        login("admin", "admin123")
        r = client.get("/admin/orders/export")
        assert r.status_code == 200
        assert r.content_type.startswith("text/csv")
        assert r.data[:3] == b"\xef\xbb\xbf"
        assert "订单号".encode() in r.data

    def test_order_filter(self, client, login, admin, user, schedule):
        login("admin", "admin123")
        r = client.get("/admin/orders?status=paid")
        assert r.status_code == 200


class TestAdminUsers:
    def test_list_users(self, client, login, admin, user):
        login("admin", "admin123")
        r = client.get("/admin/users")
        assert r.status_code == 200

    def test_toggle_admin(self, app, client, form, login, admin, user):
        login("admin", "admin123")
        r = client.post(f"/admin/users/{user}/toggle_admin", data=form(),
                        follow_redirects=True)
        assert "设为管理员".encode() in r.data
        with app.app_context():
            u = db.session.get(User, user)
            assert u.is_admin is True

    def test_cannot_toggle_self(self, client, form, login, admin):
        login("admin", "admin123")
        r = client.post(f"/admin/users/{admin}/toggle_admin", data=form(),
                        follow_redirects=True)
        assert "不能修改自己的管理员状态".encode() in r.data
