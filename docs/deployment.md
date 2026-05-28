# 部署说明

## 运行环境

| 依赖 | 版本 |
|------|------|
| Python | ≥ 3.11 |
| pip | 最新版 |
| SQLite | Python 内置 |
| Gunicorn | ≥ 23.0（生产环境） |

## 方式一：直接运行（开发/测试）

### 1. 克隆代码

```bash
git clone https://github.com/TD-ding/car-ticket-platform.git
cd car-ticket-platform
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 初始化数据库并启动

```bash
# 初始化示例数据（创建管理员和测试班次）
python init_db.py

# 启动开发服务器
python app.py
```

应用运行在 `http://localhost:5000`。

默认账号：
- 管理员：`admin` / `admin123`
- 测试用户：`张三` / `李四` / `王五`，密码均为 `123456`

### 5. 运行测试

```bash
pip install pytest flake8

# 运行单元测试（73 个测试用例）
pytest tests/ -v

# 运行代码检查
flake8 app.py models.py config.py init_db.py tests/ --max-line-length=120
```

## 方式二：Docker 部署（生产推荐）

### 1. 构建并启动

```bash
docker compose up -d --build
```

应用运行在 `http://localhost:5000`。

### 2. 初始化数据

```bash
docker compose exec web python init_db.py
```

### 3. 查看日志

```bash
docker compose logs -f web
```

### 4. 停止

```bash
docker compose down
```

数据保存在 Docker volume `db-data` 中，`down` 不会删除数据。彻底清除：

```bash
docker compose down -v
```

## 方式三：Gunicorn 直接部署

```bash
pip install -r requirements.txt
python init_db.py
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app
```

建议搭配 Nginx 反向代理。

## 配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SECRET_KEY` | 自动生成 `.secret_key` 文件 | Flask 会话加密密钥，生产环境务必设置固定值 |
| `DATABASE_URL` | `sqlite:///instance/car_ticket.db` | 数据库连接串，支持 PostgreSQL |
| `GUNICORN_WORKERS` | `4` | Gunicorn 工作进程数 |

### 使用 .env 文件

复制示例配置并修改：

```bash
cp .env.example .env
# 编辑 .env 设置生产环境密钥和数据库
```

> `.env` 文件已被 `.gitignore` 排除，不会提交到代码仓库。

### PostgreSQL 配置示例

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/car_ticket
```

切换到 PostgreSQL 需要额外安装驱动：

```bash
pip install psycopg2-binary
```

## CI/CD

### CI（持续集成）

`.github/workflows/ci.yml` 在 push/PR 时自动运行：

1. Python 3.11 + 3.12 矩阵测试
2. flake8 代码检查
3. pytest 单元测试
4. Docker 镜像构建验证

### CD（持续部署）

`.github/workflows/cd.yml` 在 main 分支 push 时运行：

1. 运行测试
2. 构建 Docker 镜像
3. 推送到 Docker Hub（需配置 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN` secrets）

## 目录结构

```
car-ticket-platform/
├── app.py              # 主应用（路由、业务逻辑）
├── config.py           # 配置类
├── models.py           # 数据模型
├── init_db.py          # 数据库初始化和示例数据
├── requirements.txt    # Python 依赖
├── Dockerfile          # Docker 镜像定义
├── docker-compose.yml  # Docker Compose 编排
├── .env.example        # 环境变量示例
├── .gitignore
├── .dockerignore
├── setup.cfg           # pytest 配置
├── tests/              # 单元测试
│   ├── conftest.py     # 测试配置和 fixtures
│   ├── test_auth.py    # 认证测试
│   ├── test_booking.py # 订票/取消/候补测试
│   ├── test_admin.py   # 管理后台测试
│   └── test_pages.py   # 页面/搜索/收藏测试
├── templates/          # Jinja2 模板
├── static/             # 静态资源
│   ├── css/style.css
│   └── js/main.js
├── docs/               # 项目文档
└── instance/           # SQLite 数据库文件（gitignore）
```
