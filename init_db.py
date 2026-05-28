"""Seed the database with sample data."""
from app import app, db, _migrate_db
from models import User, Schedule, Order
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

PLACES = [
    "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京",
    "重庆", "西安", "苏州", "天津", "长沙", "郑州", "青岛",
]


def seed():
    with app.app_context():
        _migrate_db()

        # Admin user
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                is_admin=True,
                real_name="系统管理员",
            ))

        # Demo users
        for name in ("张三", "李四", "王五"):
            username = name
            if not User.query.filter_by(username=username).first():
                db.session.add(User(
                    username=username,
                    password_hash=generate_password_hash("123456"),
                    real_name=name,
                    phone=f"138{random.randint(10000000, 99999999)}",
                ))

        db.session.commit()

        # Sample schedules
        if Schedule.query.count() == 0:
            now = datetime.now()
            for i in range(30):
                dep = random.choice(PLACES)
                dest = random.choice([p for p in PLACES if p != dep])
                hours = random.randint(2, 12)
                dep_time = now + timedelta(days=random.randint(0, 14), hours=random.randint(6, 18))
                arr_time = dep_time + timedelta(hours=hours)
                price = round(random.uniform(50, 500), 1)
                seats = random.choice([30, 40, 45, 50])
                db.session.add(Schedule(
                    departure=dep,
                    destination=dest,
                    departure_time=dep_time,
                    arrival_time=arr_time,
                    price=price,
                    total_seats=seats,
                    available_seats=random.randint(0, seats),
                ))
            db.session.commit()

        print("数据库初始化完成！")
        print("管理员: admin / admin123")
        print("测试用户: 张三/李四/王五, 密码: 123456")


if __name__ == "__main__":
    seed()
