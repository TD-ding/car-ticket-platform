from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, abort,
)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Schedule, Order
from functools import wraps
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not password:
            flash("用户名和密码不能为空", "danger")
            return redirect(url_for("register"))
        if password != confirm:
            flash("两次密码不一致", "danger")
            return redirect(url_for("register"))
        if User.query.filter_by(username=username).first():
            flash("用户名已存在", "danger")
            return redirect(url_for("register"))

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        flash("注册成功，请登录", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get("next")
            flash("登录成功", "success")
            return redirect(next_page or (url_for("admin_dashboard") if user.is_admin else url_for("index")))
        flash("用户名或密码错误", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已退出登录", "info")
    return redirect(url_for("index"))


# ── Public Pages ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    schedules = Schedule.query.filter(
        Schedule.status == "active",
        Schedule.available_seats > 0,
        Schedule.departure_time > datetime.now(),
    ).order_by(Schedule.departure_time).limit(20).all()
    return render_template("index.html", schedules=schedules)


@app.route("/search")
def search():
    departure = request.args.get("departure", "").strip()
    destination = request.args.get("destination", "").strip()
    date = request.args.get("date", "").strip()

    query = Schedule.query.filter(
        Schedule.status == "active",
        Schedule.departure_time > datetime.now(),
    )
    if departure:
        query = query.filter(Schedule.departure.ilike(f"%{departure}%"))
    if destination:
        query = query.filter(Schedule.destination.ilike(f"%{destination}%"))
    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d")
            next_day = d + timedelta(days=1)
            query = query.filter(
                Schedule.departure_time >= d,
                Schedule.departure_time < next_day,
            )
        except ValueError:
            pass

    schedules = query.order_by(Schedule.departure_time).all()
    return render_template("search.html", schedules=schedules,
                           departure=departure, destination=destination, date=date)


# ── Booking ───────────────────────────────────────────────────────────────────

@app.route("/schedule/<int:schedule_id>")
def schedule_detail(schedule_id):
    schedule = db.session.get(Schedule, schedule_id)
    if not schedule:
        abort(404)
    return render_template("schedule_detail.html", schedule=schedule)


@app.route("/book/<int:schedule_id>", methods=["GET", "POST"])
@login_required
def book(schedule_id):
    schedule = db.session.get(Schedule, schedule_id)
    if not schedule or schedule.status != "active":
        flash("该班次不可预订", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        if schedule.available_seats <= 0:
            flash("该班次已满", "danger")
            return redirect(url_for("schedule_detail", schedule_id=schedule_id))

        passenger_name = request.form.get("passenger_name", "").strip()
        passenger_phone = request.form.get("passenger_phone", "").strip()
        if not passenger_name or not passenger_phone:
            flash("请填写乘车人信息", "danger")
            return redirect(url_for("book", schedule_id=schedule_id))

        seat_number = schedule.total_seats - schedule.available_seats + 1
        order = Order(
            user_id=current_user.id,
            schedule_id=schedule_id,
            passenger_name=passenger_name,
            passenger_phone=passenger_phone,
            seat_number=seat_number,
        )
        schedule.available_seats -= 1
        db.session.add(order)
        db.session.commit()
        flash(f"订票成功！座位号: {seat_number}", "success")
        return redirect(url_for("my_orders"))

    return render_template("booking.html", schedule=schedule)


@app.route("/my_orders")
@login_required
def my_orders():
    orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("my_orders.html", orders=orders)


@app.route("/order/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):
    order = db.session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        abort(403)
    if order.order_status != "paid":
        flash("该订单无法取消", "danger")
        return redirect(url_for("my_orders"))

    order.order_status = "cancelled"
    order.schedule.available_seats += 1
    db.session.commit()
    flash("订单已取消", "success")
    return redirect(url_for("my_orders"))


# ── Admin: Schedules ─────────────────────────────────────────────────────────

@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "users": User.query.count(),
        "schedules": Schedule.query.filter_by(status="active").count(),
        "orders": Order.query.filter_by(order_status="paid").count(),
        "revenue": db.session.query(
            db.func.sum(Schedule.price)
        ).join(Order).filter(Order.order_status == "paid").scalar() or 0,
    }
    return render_template("admin/dashboard.html", stats=stats)


@app.route("/admin/schedules")
@admin_required
def admin_schedules():
    schedules = Schedule.query.order_by(Schedule.departure_time.desc()).all()
    return render_template("admin/schedules.html", schedules=schedules)


@app.route("/admin/schedules/new", methods=["GET", "POST"])
@admin_required
def admin_schedule_new():
    if request.method == "POST":
        s = Schedule(
            departure=request.form["departure"],
            destination=request.form["destination"],
            departure_time=datetime.strptime(request.form["departure_time"], "%Y-%m-%dT%H:%M"),
            arrival_time=datetime.strptime(request.form["arrival_time"], "%Y-%m-%dT%H:%M"),
            price=float(request.form["price"]),
            total_seats=int(request.form.get("total_seats", 40)),
            available_seats=int(request.form.get("total_seats", 40)),
        )
        db.session.add(s)
        db.session.commit()
        flash("班次已添加", "success")
        return redirect(url_for("admin_schedules"))
    return render_template("admin/schedule_form.html", schedule=None)


@app.route("/admin/schedules/<int:schedule_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_schedule_edit(schedule_id):
    schedule = db.session.get(Schedule, schedule_id)
    if not schedule:
        abort(404)
    if request.method == "POST":
        schedule.departure = request.form["departure"]
        schedule.destination = request.form["destination"]
        schedule.departure_time = datetime.strptime(request.form["departure_time"], "%Y-%m-%dT%H:%M")
        schedule.arrival_time = datetime.strptime(request.form["arrival_time"], "%Y-%m-%dT%H:%M")
        schedule.price = float(request.form["price"])
        schedule.total_seats = int(request.form.get("total_seats", 40))
        db.session.commit()
        flash("班次已更新", "success")
        return redirect(url_for("admin_schedules"))
    return render_template("admin/schedule_form.html", schedule=schedule)


@app.route("/admin/schedules/<int:schedule_id>/cancel", methods=["POST"])
@admin_required
def admin_schedule_cancel(schedule_id):
    schedule = db.session.get(Schedule, schedule_id)
    if not schedule:
        abort(404)
    schedule.status = "cancelled"
    db.session.commit()
    flash("班次已取消", "success")
    return redirect(url_for("admin_schedules"))


# ── Admin: Orders ─────────────────────────────────────────────────────────────

@app.route("/admin/orders")
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=orders)


@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_order_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    new_status = request.form.get("status")
    if new_status in ("paid", "used", "cancelled"):
        old_status = order.order_status
        order.order_status = new_status
        if new_status == "cancelled" and old_status != "cancelled":
            order.schedule.available_seats += 1
        elif new_status == "paid" and old_status == "cancelled":
            order.schedule.available_seats -= 1
        db.session.commit()
        flash("订单状态已更新", "success")
    return redirect(url_for("admin_orders"))


# ── Admin: Users ──────────────────────────────────────────────────────────────

@app.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@app.route("/admin/users/<int:user_id>/toggle_admin", methods=["POST"])
@admin_required
def admin_toggle_admin(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash("不能修改自己的管理员状态", "danger")
        return redirect(url_for("admin_users"))
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"已{'设为管理员' if user.is_admin else '取消管理员'}", "success")
    return redirect(url_for("admin_users"))


# ── API (JSON) ────────────────────────────────────────────────────────────────

@app.route("/api/schedules")
def api_schedules():
    schedules = Schedule.query.filter(
        Schedule.status == "active",
        Schedule.departure_time > datetime.now(),
    ).order_by(Schedule.departure_time).all()
    return jsonify([{
        "id": s.id,
        "departure": s.departure,
        "destination": s.destination,
        "departure_time": s.departure_time.isoformat(),
        "arrival_time": s.arrival_time.isoformat(),
        "price": s.price,
        "available_seats": s.available_seats,
    } for s in schedules])


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# ── Init ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                is_admin=True,
                real_name="系统管理员",
            )
            db.session.add(admin)
            db.session.commit()
            print("管理员账号已创建: admin / admin123")
    app.run(debug=True, port=5000)
