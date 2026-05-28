"""Tests for booking, order cancellation, and waitlist auto-fulfill."""
from app import db
from models import Schedule, Order, Waitlist
from datetime import datetime, timedelta


class TestBooking:
    def test_booking_page(self, client, form, login, user, schedule):
        login("testuser")
        r = client.get(f"/book/{schedule}")
        assert r.status_code == 200
        assert "预订车票".encode() in r.data

    def test_booking_success(self, app, client, form, login, user, schedule):
        login("testuser")
        r = client.post(f"/book/{schedule}", data=form(
            passenger_name="测试", passenger_phone="13800000000",
        ), follow_redirects=False)
        assert r.status_code == 302
        assert "/booking_success/" in r.headers["Location"]

        with app.app_context():
            s = db.session.get(Schedule, schedule)
            assert s.available_seats == 4

    def test_booking_empty_fields(self, client, form, login, user, schedule):
        login("testuser")
        r = client.post(f"/book/{schedule}", data=form(
            passenger_name="", passenger_phone="",
        ), follow_redirects=True)
        assert "请填写乘车人信息".encode() in r.data

    def test_booking_duplicate(self, client, form, login, user, schedule):
        login("testuser")
        client.post(f"/book/{schedule}", data=form(
            passenger_name="测试", passenger_phone="13800000000",
        ))
        r = client.post(f"/book/{schedule}", data=form(
            passenger_name="测试", passenger_phone="13800000000",
        ), follow_redirects=True)
        assert "不能重复订票".encode() in r.data

    def test_booking_cancelled_schedule(self, app, client, form, login, user):
        with app.app_context():
            s = Schedule(
                departure="A", destination="B",
                departure_time=datetime.now() + timedelta(days=1),
                arrival_time=datetime.now() + timedelta(days=1, hours=3),
                price=100, total_seats=10, available_seats=10,
                status="cancelled",
            )
            db.session.add(s)
            db.session.commit()
            sid = s.id
        login("testuser")
        r = client.get(f"/book/{sid}", follow_redirects=True)
        assert "该班次不可预订".encode() in r.data

    def test_booking_full_schedule(self, client, form, login, user, full_schedule):
        login("testuser")
        r = client.post(f"/book/{full_schedule}", data=form(
            passenger_name="测试", passenger_phone="13800000000",
        ), follow_redirects=True)
        assert "已满".encode() in r.data

    def test_booking_requires_login(self, client, schedule):
        r = client.get(f"/book/{schedule}", follow_redirects=False)
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]


class TestCancelOrder:
    def test_cancel_order_success(self, app, client, form, login, user, schedule):
        login("testuser")
        client.post(f"/book/{schedule}", data=form(
            passenger_name="测试", passenger_phone="13800000000",
        ))
        with app.app_context():
            order = Order.query.filter_by(user_id=user).first()
            oid = order.id
        r = client.post(f"/order/{oid}/cancel", data=form(),
                        follow_redirects=True)
        assert "订单已取消".encode() in r.data
        with app.app_context():
            o = db.session.get(Order, oid)
            assert o.order_status == "cancelled"
            s = db.session.get(Schedule, schedule)
            assert s.available_seats == 5

    def test_cancel_order_twice(self, app, client, form, login, user, schedule):
        login("testuser")
        client.post(f"/book/{schedule}", data=form(
            passenger_name="测试", passenger_phone="13800000000",
        ))
        with app.app_context():
            order = Order.query.filter_by(user_id=user).first()
            oid = order.id
        client.post(f"/order/{oid}/cancel", data=form())
        r = client.post(f"/order/{oid}/cancel", data=form(),
                        follow_redirects=True)
        assert "该订单无法取消".encode() in r.data

    def test_cancel_others_order_forbidden(self, app, client, form, login, user, user2, schedule):
        login("testuser")
        client.post(f"/book/{schedule}", data=form(
            passenger_name="测试", passenger_phone="13800000000",
        ))
        with app.app_context():
            order = Order.query.filter_by(user_id=user).first()
            oid = order.id
        login("testuser2")
        r = client.post(f"/order/{oid}/cancel", data=form())
        assert r.status_code == 403


class TestWaitlist:
    def test_waitlist_page_when_full(self, client, login, user, full_schedule):
        login("testuser")
        r = client.get(f"/waitlist/{full_schedule}")
        assert r.status_code == 200
        assert "候补订票".encode() in r.data

    def test_waitlist_joined(self, app, client, form, login, user, full_schedule):
        login("testuser")
        r = client.post(f"/waitlist/{full_schedule}", data=form(
            passenger_name="候补人", passenger_phone="13800000000",
        ), follow_redirects=True)
        assert "已加入候补队列".encode() in r.data
        with app.app_context():
            wl = Waitlist.query.filter_by(user_id=user, schedule_id=full_schedule).first()
            assert wl is not None
            assert wl.status == "waiting"

    def test_waitlist_blocked_when_seats_available(self, client, login, user, schedule):
        login("testuser")
        r = client.get(f"/waitlist/{schedule}", follow_redirects=True)
        assert "该班次仍有余票".encode() in r.data

    def test_waitlist_duplicate(self, client, form, login, user, full_schedule):
        login("testuser")
        client.post(f"/waitlist/{full_schedule}", data=form(
            passenger_name="候补人", passenger_phone="13800000000",
        ))
        r = client.get(f"/waitlist/{full_schedule}", follow_redirects=True)
        assert "已在候补队列中".encode() in r.data

    def test_waitlist_cancel(self, app, client, form, login, user, full_schedule):
        login("testuser")
        client.post(f"/waitlist/{full_schedule}", data=form(
            passenger_name="候补人", passenger_phone="13800000000",
        ))
        with app.app_context():
            wl = Waitlist.query.filter_by(user_id=user).first()
            wlid = wl.id
        r = client.post(f"/waitlist/{wlid}/cancel", data=form(),
                        follow_redirects=True)
        assert "候补已取消".encode() in r.data
        with app.app_context():
            wl = db.session.get(Waitlist, wlid)
            assert wl.status == "cancelled"

    def test_waitlist_auto_fulfill_on_cancel(self, app, client, form, login, user, user2):
        """When a user cancels, waitlisted user should auto-get a ticket."""
        with app.app_context():
            s = Schedule(
                departure="A", destination="B",
                departure_time=datetime.now() + timedelta(days=1),
                arrival_time=datetime.now() + timedelta(days=1, hours=3),
                price=100, total_seats=1, available_seats=1,
            )
            db.session.add(s)
            db.session.commit()
            sid = s.id

        # user1 books the only seat
        login("testuser")
        client.post(f"/book/{sid}", data=form(
            passenger_name="用户1", passenger_phone="13800000000",
        ))

        # user2 joins waitlist
        login("testuser2")
        client.post(f"/waitlist/{sid}", data=form(
            passenger_name="用户2", passenger_phone="13800000001",
        ))

        # user1 cancels
        login("testuser")
        with app.app_context():
            order = Order.query.filter_by(user_id=user).first()
            oid = order.id
        client.post(f"/order/{oid}/cancel", data=form())

        # user2 should now have an order
        with app.app_context():
            wl = Waitlist.query.filter_by(user_id=user2).first()
            assert wl.status == "fulfilled"
            order2 = Order.query.filter_by(user_id=user2).first()
            assert order2 is not None
            assert order2.order_status == "paid"
            s = db.session.get(Schedule, sid)
            assert s.available_seats == 0
