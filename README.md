# 🚌 汽车订票平台

一个基于 Flask + SQLite 的在线汽车票预订系统。

## 技术栈

- **前端**: HTML / CSS / JavaScript
- **后端**: Python Flask
- **数据库**: SQLite (Flask-SQLAlchemy)
- **认证**: Flask-Login

## 功能模块

### 用户端
- 注册 / 登录
- 查看近期班次
- 按出发地、目的地、日期搜索班次
- 在线订票（自动分配座位）
- 查看我的订单、取消订单

### 管理员端
- 仪表盘（用户数、班次数、订单数、营收统计）
- 班次管理（增 / 改 / 取消）
- 订单管理（修改订单状态）
- 用户管理（设置 / 取消管理员权限）

### REST API
- `GET /api/schedules` — 获取活跃班次列表（JSON）

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/TD-ding/car-ticket-platform.git
cd car-ticket-platform

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库（含示例数据）
python init_db.py

# 4. 启动服务
python app.py
```

浏览器访问 http://127.0.0.1:5000

## 测试账号

| 角色   | 用户名   | 密码     |
|--------|----------|----------|
| 管理员 | admin    | admin123 |
| 用户   | 张三     | 123456   |
| 用户   | 李四     | 123456   |
| 用户   | 王五     | 123456   |

## 项目结构

```
car-ticket-platform/
├── app.py                  # Flask 主应用（路由 & 业务逻辑）
├── config.py               # 配置
├── models.py               # 数据模型（User / Schedule / Order）
├── init_db.py              # 数据库初始化 & 示例数据
├── requirements.txt        # Python 依赖
├── static/
│   ├── css/style.css       # 样式
│   └── js/main.js          # 前端脚本
├── templates/              # Jinja2 模板
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── search.html
│   ├── schedule_detail.html
│   ├── booking.html
│   ├── my_orders.html
│   ├── 403.html
│   ├── 404.html
│   └── admin/
│       ├── dashboard.html
│       ├── schedules.html
│       ├── schedule_form.html
│       ├── orders.html
│       └── users.html
└── instance/
    └── car_ticket.db       # SQLite 数据库（运行后自动生成）
```
