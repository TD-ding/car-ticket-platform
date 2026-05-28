import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SECRET_KEY_FILE = os.path.join(BASE_DIR, ".secret_key")


def _load_or_create_secret_key():
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    try:
        with open(SECRET_KEY_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        key = secrets.token_hex(32)
        with open(SECRET_KEY_FILE, "w") as f:
            f.write(key)
        return key


class Config:
    SECRET_KEY = _load_or_create_secret_key()
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "car_ticket.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
