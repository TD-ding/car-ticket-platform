from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    real_name = db.Column(db.String(80), default="")
    phone = db.Column(db.String(20), default="")
    email = db.Column(db.String(120), default="")
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", backref="user", lazy=True)


class Schedule(db.Model):
    __tablename__ = "schedules"

    id = db.Column(db.Integer, primary_key=True)
    departure = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_seats = db.Column(db.Integer, nullable=False, default=40)
    available_seats = db.Column(db.Integer, nullable=False, default=40)
    status = db.Column(db.String(20), default="active")  # active / cancelled

    orders = db.relationship("Order", backref="schedule", lazy=True)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedules.id"), nullable=False)
    passenger_name = db.Column(db.String(80), nullable=False)
    passenger_phone = db.Column(db.String(20), nullable=False)
    seat_number = db.Column(db.Integer, nullable=False)
    order_status = db.Column(db.String(20), default="paid")  # paid / cancelled / used
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
