# 后端架构

## 技术栈

- Python 3.11+
- Flask 3.1 + Flask-Login 0.6 + Flask-SQLAlchemy 3.1
- SQLAlchemy 2.0（ORM + Core）
- SQLite（可通过环境变量切换 PostgreSQL）
- Gunicorn（生产 WSGI 服务器）

## 数据模型 (models.py)

### User

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| username | String(80) UNIQUE | 登录名，不可重复 |
| password_hash | String(256) | Werkzeug PBKDF2 哈希 |
| real_name | String(80) | 真实姓名 |
| phone | String(20) | 手机号 |
| email | String(120) | 邮箱 |
| is_admin | Boolean | 管理员标识，默认 False |
| created_at | DateTime | 注册时间 |

关联：`orders`（一对多）、`favorites`（一对多，级联删除）

### Schedule

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| departure | String(100) | 出发地 |
| destination | String(100) | 目的地 |
| departure_time | DateTime | 出发时间 |
| arrival_time | DateTime | 到达时间 |
| price | Float | 票价（元） |
| total_seats | Integer | 总座位数 |
| available_seats | Integer | 剩余座位数 |
| status | String(20) | `active` / `cancelled` |

计算属性：`sold_seats` = total_seats - available_seats

### Order

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| user_id | FK → users.id | 下单用户 |
| schedule_id | FK → schedules.id | 班次 |
| passenger_name | String(80) | 乘车人姓名 |
| passenger_phone | String(20) | 乘车人手机 |
| seat_number | Integer | 座位号 |
| price | Float | 订单票价（下单时快照） |
| order_status | String(20) | `paid` / `used` / `cancelled` |
| created_at | DateTime | 下单时间 |

### Waitlist

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| user_id | FK → users.id | 候补用户 |
| schedule_id | FK → schedules.id | 班次 |
| passenger_name | String(80) | 乘车人姓名 |
| passenger_phone | String(20) | 乘车人手机 |
| status | String(20) | `waiting` / `fulfilled` / `cancelled` |
| created_at | DateTime | 候补时间 |

索引：`(schedule_id, status)` 加速候补查询

### Favorite

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| user_id | FK → users.id | 用户 |
| schedule_id | FK → schedules.id | 班次 |
| created_at | DateTime | 收藏时间 |

唯一约束：`(user_id, schedule_id)` 每用户每班次只能收藏一次

## API 端点

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/register` | 注册，密码 ≥ 6 位 |
| GET/POST | `/login` | 登录，管理员跳转后台 |
| GET | `/logout` | 退出登录（需登录） |

### 用户中心（需登录）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/profile` | 查看/编辑个人资料 |
| GET/POST | `/change_password` | 修改密码（需旧密码） |

### 公共页面

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页（热门路线 + 近期班次） |
| GET | `/search` | 搜索班次，支持 departure/destination/date/sort 参数 |
| GET | `/schedule/<id>` | 班次详情（含收藏状态） |

### 订票（需登录）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/book/<id>` | 预订车票 |
| GET | `/booking_success/<id>` | 订票成功确认页 |
| GET | `/my_orders` | 我的订单列表 |
| POST | `/order/<id>/cancel` | 取消订单，释放座位并触发候补 |

### 候补（需登录）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/waitlist/<schedule_id>` | 加入候补（仅满座班次） |
| GET | `/my_waitlist` | 我的候补列表 |
| POST | `/waitlist/<wl_id>/cancel` | 取消候补 |

### 收藏（需登录）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/schedule/<id>/favorite` | 切换收藏（有则删，无则加） |
| GET | `/favorites` | 我的收藏列表 |

### 管理后台（需管理员）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin` | 仪表盘（用户/班次/订单/营收/候补统计） |
| GET | `/admin/schedules` | 班次列表（支持出发地/目的地/状态/日期筛选） |
| GET/POST | `/admin/schedules/new` | 添加班次 |
| GET/POST | `/admin/schedules/<id>/edit` | 编辑班次 |
| POST | `/admin/schedules/<id>/cancel` | 取消班次（关联订单自动取消） |
| POST | `/admin/schedules/<id>/copy` | 复制班次 |
| GET | `/admin/orders` | 订单列表（支持关键词/状态/日期筛选） |
| POST | `/admin/orders/<id>/status` | 修改订单状态 |
| GET | `/admin/orders/export` | 导出订单 CSV（带 BOM） |
| GET | `/admin/users` | 用户列表（支持搜索/角色筛选） |
| POST | `/admin/users/<id>/toggle_admin` | 切换管理员身份 |

### JSON API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/schedules` | 获取所有活跃未来班次（JSON 数组） |

## 核心业务逻辑

### 订票流程

1. 验证班次状态和余票（`SELECT ... FOR UPDATE` 行锁防超卖）
2. 检查重复订票
3. 生成座位号 = total_seats - available_seats + 1
4. 创建订单、扣减余票、事务提交

### 取消订单 → 候补自动出票

`cancel_order` 和 `admin_order_status` 取消订单后调用 `_process_waitlist(schedule)`：

1. 按 `created_at` 升序获取该班次所有 `waiting` 候补记录
2. 逐条处理：再次 `SELECT FOR UPDATE` 检查余票
3. 跳过已有有效订单的用户
4. 为候补用户创建订单、扣减余票、标记 `fulfilled`
5. 余票用尽时停止处理

### 管理员修改订单状态

状态转换与座位数变化规则：

| 原状态 | 新状态 | 座位变化 |
|--------|--------|----------|
| paid/used → cancelled | 释放座位 + 触发候补 |
| cancelled → paid/used | 扣减座位（满座则拒绝） |
| paid ↔ used | 不变 |

### 班次编辑验证

- `_validate_schedule_form` 校验：时间格式、到达 > 出发、价格 > 0、座位 > 0
- 额外校验：`new_total >= sold_seats`（总座位不能少于已售出数）

## 安全机制

### CSRF 保护

所有 POST 请求需携带 `csrf_token` 表单字段，值与 session 中比对。不匹配返回 403。

### 权限控制

- `@login_required`：需登录
- `@admin_required`：需管理员
- 订单操作验证 `order.user_id == current_user.id`，越权返回 403

### 密码安全

- Werkzeug `generate_password_hash` / `check_password_hash`
- PBKDF2-SHA256 算法

### SQL 注入防护

- ORM 参数化查询
- 用户输入的 LIKE 查询使用 `_escape_like()` 转义 `%`、`_`、`\`

## 搜索排序参数

`/search?sort=` 支持：

| 值 | 排序规则 |
|----|----------|
| `price_asc` | 价格升序 |
| `price_desc` | 价格降序 |
| `duration_asc` | 行程时长升序 |
| `duration_desc` | 行程时长降序 |
| 空/其他 | 出发时间升序（默认） |
