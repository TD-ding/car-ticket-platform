# 前端架构

## 技术栈

- 纯 HTML5 + CSS3 + 原生 JavaScript，无前端框架
- Jinja2 模板引擎（Flask 内置）
- 响应式设计，移动端适配

## 目录结构

```
static/
  css/style.css        # 全局样式
  js/main.js           # 全局脚本
templates/
  base.html            # 基础布局（导航栏、消息提示、页脚）
  _pagination.html     # 分页组件宏
  index.html           # 首页
  search.html          # 搜索结果页
  schedule_detail.html # 班次详情页
  booking.html         # 订票表单页
  booking_success.html # 订票成功页
  my_orders.html       # 我的订单页
  my_waitlist.html     # 我的候补页
  my_favorites.html    # 我的收藏页
  waitlist.html        # 候补订票表单页
  login.html           # 登录页
  register.html        # 注册页
  profile.html         # 个人资料页
  change_password.html # 修改密码页
  403.html / 404.html  # 错误页
  admin/               # 管理后台模板
```

## 基础布局 (base.html)

所有页面继承 `base.html`，包含三个区域：

- **导航栏** (`.navbar`)：品牌名、首页、查询班次、我的订单/候补/收藏（登录后显示）、管理后台（管理员显示）、用户名、登录/注册或退出按钮
- **内容区** (`<main class="container">`)：Flash 消息 + 各页面内容
- **页脚** (`.footer`)：版权信息

移动端通过汉堡菜单 `.nav-toggle` 切换导航。

## 页面说明

### 首页 (index.html)

| 区域 | 说明 |
|------|------|
| Hero 搜索栏 | 出发地 → 目的地 + 日期，提交到 `/search` |
| 热门路线 | 按历史订单量统计的 TOP 6 路线卡片，点击跳转搜索 |
| 近期班次 | 分页展示未来可预订的班次卡片 |

### 搜索结果页 (search.html)

- 搜索表单：出发地、目的地、日期、排序方式（默认/价格升降/时长升降）
- 搜索摘要：显示筛选条件 + `pagination.total` 总结果数
- 班次列表：卡片网格，显示路线、时间、票价、余票

### 班次详情页 (schedule_detail.html)

- 路线信息：出发/到达时间、票价、座位数、状态
- 收藏按钮（登录用户可见）
- 操作按钮逻辑：
  - 班次已取消 → 显示"班次已取消"
  - 有余票 → "立即订票"
  - 无余票且已登录 → "候补订票"
  - 无余票且未登录 → "已售罄"

### 订票流程

1. `booking.html`：填写乘车人姓名、手机号
2. `booking_success.html`：显示订单号、座位号、路线信息

### 候补流程

1. `waitlist.html`：班次满时填写候补信息
2. `my_waitlist.html`：查看候补状态（等待中/已出票/已取消），可取消候补

### 用户中心

- `my_orders.html`：订单列表，已过期行淡化，可取消未出行订单
- `my_favorites.html`：收藏班次列表，可快速订票/候补或取消收藏
- `profile.html`：编辑姓名、手机、邮箱
- `change_password.html`：修改密码（需旧密码验证）

## 通用组件

### 班次卡片 (`.schedule-card`)

在首页、搜索页、收藏页使用，显示：
- 路线：出发地 → 目的地 + 时长徽章
- 元信息：出发时间、票价、余票（<10 红色警告）

### 分页 (`_pagination.html`)

Jinja2 宏 `render_pagination(pagination)`，接收 Flask-SQLAlchemy 分页对象，渲染上一页/下一页按钮和页码信息。

## 样式规范

| 类名 | 用途 |
|------|------|
| `.btn-primary` | 主操作按钮（蓝色） |
| `.btn-outline` | 次要操作（蓝色边框） |
| `.btn-danger` | 危险操作（红色） |
| `.btn-warning` | 候补/警示（橙色） |
| `.btn-disabled` | 禁用状态（灰色） |
| `.badge-success/danger/warning` | 状态标签 |
| `.alert-success/danger/info/warning` | Flash 消息 |
| `.text-danger / .text-success` | 红/绿色文本 |
| `.price` | 红色加粗价格 |

## JavaScript (main.js)

三个功能：
1. Flash 消息 4 秒自动淡出消失
2. 表单提交防重复点击（按钮禁用 5 秒）
3. 移动端汉堡菜单切换
