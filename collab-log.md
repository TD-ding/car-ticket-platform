# 汽车订票平台 — 协作迭代日志

## 项目概述

汽车订票平台是一个基于 Flask 的 Web 应用，提供汽车票在线预订、候补排队、班次管理、订单管理等功能。面向旅客（查询、订票、收藏、候补）和管理员（班次 CRUD、订单管理、数据导出）两类用户。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11+ / Flask 3.1 / Flask-Login 0.6 / Flask-SQLAlchemy 3.1 |
| 数据库 | SQLite（默认）/ PostgreSQL（可选） |
| 前端 | HTML5 + CSS3 + 原生 JavaScript（无框架） |
| 模板 | Jinja2 |
| 部署 | Gunicorn / Docker Compose |
| CI/CD | GitHub Actions（flake8 + pytest + Docker build） |
| 测试 | pytest（73 个测试用例） |

---

## 迭代记录

### 第 1 轮：feat — 初始版本

**分支**: `agent/round1` | **PR**: #1

初始化项目，包含基础的用户注册登录、班次展示、订票、管理后台功能。

**主要改动**:
- Flask 项目骨架（`app.py` / `config.py` / `models.py`）
- `User`、`Schedule`、`Order` 三个核心数据模型
- 公共页面：首页、搜索、班次详情、订票流程
- 管理后台：仪表盘、班次管理（增删改）、订单管理、用户管理
- 用户系统：注册、登录、退出
- CSRF 保护、管理员权限控制

---

### 第 2 轮：refactor — 代码质量优化

**分支**: `agent/round1` | **PR**: #2

修复首轮代码中的安全漏洞和功能缺陷。

**主要改动**:
- 搜索日期范围计算 bug 修复（使用 `timedelta` 替代手动日期计算）
- 表单校验增强（时间格式、价格范围、到达必须晚于出发）
- 座位数联动（编辑班次时自动调整 `available_seats`）
- 重复订票检查
- 取消班次时关联订单自动取消
- 无障碍优化（ARIA 标签、focus 样式）
- 订票确认页增加详细信息
- 移动端响应式优化
- 表单防重复提交（按钮禁用）

---

### 第 3 轮：feat — 用户体验优化

**分支**: `agent/round1` | **PR**: #3

提升用户操作的流畅度和信息展示的完整性。

**主要改动**:
- 订票表单数据保留（提交失败不丢输入）
- 搜索条件回显（出发地/目的地/日期保留在表单中）
- 行程时长显示（Jinja2 自定义 `duration` 过滤器）
- 订单列表过期标记（已过期行淡化显示）
- 管理员操作确认对话框
- 个人资料编辑页面
- 修改密码功能（旧密码验证 + 新密码 ≥ 6 位）
- 移动端汉堡菜单

---

### 第 4 轮：feat — 功能增强

**分支**: `agent/round1` | **PR**: #4, #5

7 项新功能 + 管理后台增强。

**主要改动**:
1. **候补订票** — 班次售罄后可排队，有人取消自动按 FIFO 出票（`Waitlist` 模型、`_process_waitlist` 逻辑）
2. **首页热门路线** — 按历史订单量统计 TOP 6 路线卡片
3. **搜索排序** — 支持按价格/时长升序或降序
4. **班次收藏** — `Favorite` 模型，详情页收藏按钮，收藏列表页
5. **管理后台搜索筛选** — 班次/订单/用户列表均支持多条件筛选
6. **班次复制** — 管理员一键复制班次信息到新班次
7. **订单导出 CSV** — 按筛选条件导出，UTF-8 BOM 兼容 Excel
8. 管理后台用户搜索筛选、订单导出关键词过滤、收藏跳转 `request.referrer` 优化

**新增数据模型**: `Waitlist`、`Favorite`

---

### 第 5 轮：fix — Bug 修复

**分支**: `agent/round1` | **PR**: #5（续）

修复用户反馈的 8 个 bug。

**主要改动**:
1. **管理员改订单状态** — 重写状态转换逻辑：`paid↔used` 不动座位，`cancelled→paid/used` 检查余票（满座拒绝），任意→`cancelled` 释放座位并触发候补
2. **时区统一** — 所有模型 `default` 从 `datetime.utcnow` 改为 `datetime.now`
3. **编辑班次总座位** — 新增校验 `new_total >= sold_seats`
4. **候补页面检查余票** — 有余票时 redirect 到订票页
5. **注册密码长度** — 新增最少 6 位限制
6. **搜索结果数量** — `schedules|length` → `pagination.total`
7. **CSV 导出 BOM** — 写入实际 BOM 字节 `\xef\xbb\xbf`
8. **已取消班次详情** — 优先显示"班次已取消"而非"已售罄"

---

### Step 4：测试 + Docker + CI

**分支**: `agent/lint-test-docker-ci` | **PR**: #6

建立完整的测试和部署基础设施。

**主要改动**:
- **pytest 测试套件**（73 个测试用例）：
  - `test_auth.py`（19）：注册/登录/登出/改密码
  - `test_booking.py`（14）：订票/取消/候补加入/候补自动出票
  - `test_admin.py`（21）：权限/班次 CRUD/订单状态/导出/用户管理
  - `test_pages.py`（19）：首页/搜索排序/详情/收藏/个人资料/API/错误页
- **Dockerfile** — Python 3.12-slim + Gunicorn 4 worker
- **docker-compose.yml** — 一键启动，数据持久化
- **`.dockerignore` / `.env.example`** — 配套文件
- **CI 工作流**（`.github/workflows/ci.yml`）— Python 3.11+3.12 矩阵、flake8、pytest、Docker build
- **CD 工作流**（`.github/workflows/cd.yml`）— main 分支自动测试 + Docker 镜像推送
- `requirements.txt` 添加 `gunicorn`

---

### CI 修复

**分支**: `agent/fix-ci-test-db` | **PR**: #7

修复 CI 环境下测试全部失败的问题。

**问题**: `sqlite3.OperationalError: unable to open database file`。`instance/` 目录被 `.gitignore` 排除，CI 里不存在；`config.py` 在模块导入时将 `SQLALCHEMY_DATABASE_URI` 设为文件路径，导致 Flask-SQLAlchemy 尝试打开不存在的文件。

**修复**: 在 `tests/conftest.py` 中，于 `from app import ...` 之前设置 `os.environ["DATABASE_URL"] = "sqlite:///:memory:"`，确保 app 导入时直接使用内存数据库。

---

### Step 5：文档

**分支**: `agent/docs` | **PR**: #8

编写完整的项目文档。

**新增文件**:
- `docs/frontend.md` — 前端架构、22 个页面说明、组件、样式规范、JS 功能
- `docs/backend.md` — API 端点（27 个路由）、5 个数据模型、核心业务逻辑、安全机制
- `docs/admin-frontend.md` — 管理后台各模块功能说明
- `docs/deployment.md` — 三种部署方式、配置、CI/CD、目录结构

---

## 最终状态

| 指标 | 数值 |
|------|------|
| 已合并 PR | 8 |
| Python 文件 | 4（app / models / config / init_db） |
| 模板文件 | 22 |
| 数据模型 | 5（User / Schedule / Order / Waitlist / Favorite） |
| API 端点 | 27 |
| 单元测试 | 73 |
| 文档 | 4（frontend / backend / admin / deployment） |
| CI 状态 | 通过 |
