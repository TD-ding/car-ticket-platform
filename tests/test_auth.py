"""Tests for authentication: register, login, logout, password change."""


class TestRegister:
    def test_register_page(self, client):
        r = client.get("/register")
        assert r.status_code == 200
        assert "注册".encode() in r.data

    def test_register_success(self, client, form):
        r = client.post("/register", data=form(
            username="newuser", password="123456", confirm_password="123456",
        ), follow_redirects=True)
        assert r.status_code == 200
        assert "注册成功".encode() in r.data

    def test_register_empty_username(self, client, form):
        r = client.post("/register", data=form(
            username="", password="123456", confirm_password="123456",
        ), follow_redirects=True)
        assert "用户名和密码不能为空".encode() in r.data

    def test_register_empty_password(self, client, form):
        r = client.post("/register", data=form(
            username="user1", password="", confirm_password="",
        ), follow_redirects=True)
        assert "用户名和密码不能为空".encode() in r.data

    def test_register_password_mismatch(self, client, form):
        r = client.post("/register", data=form(
            username="user1", password="123456", confirm_password="654321",
        ), follow_redirects=True)
        assert "两次密码不一致".encode() in r.data

    def test_register_short_password(self, client, form):
        r = client.post("/register", data=form(
            username="user1", password="123", confirm_password="123",
        ), follow_redirects=True)
        assert "密码至少6位".encode() in r.data

    def test_register_duplicate_username(self, client, form, user):
        r = client.post("/register", data=form(
            username="testuser", password="123456", confirm_password="123456",
        ), follow_redirects=True)
        assert "用户名已存在".encode() in r.data


class TestLogin:
    def test_login_page(self, client):
        r = client.get("/login")
        assert r.status_code == 200

    def test_login_success(self, client, form, user):
        r = client.post("/login", data=form(
            username="testuser", password="123456",
        ), follow_redirects=True)
        assert r.status_code == 200
        assert "登录成功".encode() in r.data

    def test_login_wrong_password(self, client, form, user):
        r = client.post("/login", data=form(
            username="testuser", password="wrong",
        ), follow_redirects=True)
        assert "用户名或密码错误".encode() in r.data

    def test_login_nonexistent_user(self, client, form):
        r = client.post("/login", data=form(
            username="ghost", password="123456",
        ), follow_redirects=True)
        assert "用户名或密码错误".encode() in r.data


class TestLogout:
    def test_logout(self, client, login, user):
        login("testuser")
        r = client.get("/logout", follow_redirects=True)
        assert "已退出登录".encode() in r.data

    def test_logout_requires_login(self, client):
        r = client.get("/logout", follow_redirects=False)
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]


class TestChangePassword:
    def test_change_password_page_requires_login(self, client):
        r = client.get("/change_password", follow_redirects=False)
        assert r.status_code == 302

    def test_change_password_success(self, client, form, login, user):
        login("testuser")
        r = client.post("/change_password", data=form(
            old_password="123456", new_password="654321", confirm_password="654321",
        ), follow_redirects=True)
        assert "密码已修改".encode() in r.data

    def test_change_password_wrong_old(self, client, form, login, user):
        login("testuser")
        r = client.post("/change_password", data=form(
            old_password="wrong", new_password="654321", confirm_password="654321",
        ), follow_redirects=True)
        assert "当前密码不正确".encode() in r.data

    def test_change_password_too_short(self, client, form, login, user):
        login("testuser")
        r = client.post("/change_password", data=form(
            old_password="123456", new_password="123", confirm_password="123",
        ), follow_redirects=True)
        assert "新密码至少6位".encode() in r.data

    def test_change_password_mismatch(self, client, form, login, user):
        login("testuser")
        r = client.post("/change_password", data=form(
            old_password="123456", new_password="654321", confirm_password="111111",
        ), follow_redirects=True)
        assert "两次新密码不一致".encode() in r.data
