# 本文件已归档

本文件已归档，当前项目以根目录 AGENTS.md 和《统一工单池_含OSS融合_技术与实施总规划.md》为准。

# anbo_wx 后续任务清单

## 当前状态
- Task 1 已完成：项目梳理、后端基础工程、数据库模型、迁移、初始化脚本、服务器部署测试。
- OSS 用户 Excel 已重导：
  - 组织层级严格按 Excel：`地市` = 1 级，`分公司` = 2 级，`部门` = 3 级。
  - 已移除错误的 `Excel导入组织`。
  - 手机号缺失、格式错误、重复的用户不导入。
  - 当前导入有效 OSS 用户 966 个。
- 当前服务器项目目录：`/home/yvesyuan/PycharmProjects/anbo_wx`
- 当前数据库：`anbo_wx`
- 当前分支：`main`

## Task 2 - 登录认证、JWT、OSS 绑定、首次改密
状态：DONE

目标：完成用户登录主流程。

后端 TODO：
- 实现统一响应工具 `responses.py`。
- 实现 JWT 签发和校验。
- 实现认证装饰器 `decorators.py`。
- 实现权限基础服务 `permission_service.py`。
- 实现认证服务 `auth_service.py`。
- 实现 OSS 校验服务 `oss_service.py`。
- 实现 `POST /api/auth/login`。
- 实现 `POST /api/auth/bind-oss`。
- 实现 `POST /api/auth/change-password`。
- 实现 `GET /api/auth/me`。
- 实现 `POST /api/auth/logout`。
- 登录成功/失败写入 `login_logs`。
- OSS 绑定和改密写入 `operation_logs`。

前端 TODO：
- 新增/调整登录页。
- 新增 OSS 账号确认页。
- 新增首次修改密码页。
- 新增/调整 `utils/request.js`。
- 新增/调整 `utils/auth.js`。
- 登录后按 `next_action` 跳转。

验证 TODO：
- 服务器 curl 测试登录接口。
- 测试手机号登录。
- 测试 OSS 账号登录。
- 测试初始密码用户进入 OSS 绑定或首次改密。
- 更新 `docs/api.md`、`docs/task-log.md`、`CHANGELOG.md`。
- 提交 GitHub。
- 服务器同步并确认后等待用户确认。

## Task 3 - 组织管理与菜单管理
状态：DONE

目标：完成固定三层组织管理和 `app_menus` 菜单管理。

后端 TODO：
- 实现 `GET /api/workbench/apps`，从 `app_menus` 表读取菜单。
- 实现角色等级过滤：`normal_user < org_admin < super_admin`。
- 实现用户类型过滤：当前用户类型或 `all`。
- 实现 `GET /api/admin/orgs/tree`。
- 实现 `POST /api/admin/orgs`。
- 实现 `PUT /api/admin/orgs/{id}`。
- 实现 `POST /api/admin/orgs/{id}/disable`。
- 实现 `GET /api/admin/menus`。
- 实现 `POST /api/admin/menus`。
- 实现 `PUT /api/admin/menus/{id}`。
- 实现 `POST /api/admin/menus/{id}/enable`。
- 实现 `POST /api/admin/menus/{id}/disable`。
- 保证组织只允许三层。
- 保证组织禁用不物理删除。
- 管理操作写入 `operation_logs`。

前端 TODO：
- 新增组织管理页。
- 新增菜单管理页。
- 首页先从 `/api/workbench/apps` 拉取菜单并渲染。
- 首页菜单不得写死。
- 未完成页面点击提示“功能开发中，敬请期待”。

验证 TODO：
- super_admin 可管理全部组织和菜单。
- org_admin 只能查看管理范围内组织树。
- normal_user 不可访问组织/菜单管理接口。
- 服务器 curl 测试组织和菜单接口。
- 更新 `docs/api.md`、`docs/task-log.md`、`CHANGELOG.md`。
- 提交 GitHub。
- 服务器同步并确认后等待用户确认。

## Task 4 - 用户管理
状态：DONE

目标：完成用户管理 MVP。

后端 TODO：
- 实现 `GET /api/admin/users`。
- 实现 `POST /api/admin/users`。
- 实现 `PUT /api/admin/users/{id}`。
- 实现 `POST /api/admin/users/{id}/disable`。
- 实现 `POST /api/admin/users/{id}/enable`。
- 实现 `POST /api/admin/users/{id}/reset-password`。
- 支持筛选：姓名、手机号、OSS 账号、组织、角色、状态、OSS 绑定状态。
- super_admin 可管理全部用户。
- org_admin 只能管理 `manage_org_id` 及下级组织内的 `internal + normal_user`。
- org_admin 不允许创建或编辑为 `org_admin` / `super_admin`。
- normal_user 不可访问用户管理。
- 不允许禁用最后一个 super_admin。
- 新增用户初始密码：手机号后四位 + `@jscn`。
- 有 OSS 账号时 `oss_bind_status=pending`。
- 无 OSS 账号时 `oss_bind_status=unbound`。
- 用户管理操作写入 `operation_logs`。

前端 TODO：
- 新增用户管理列表页。
- 新增用户编辑页。
- 实现搜索和筛选。
- 实现新增用户。
- 实现编辑用户。
- 实现启用/禁用。
- 实现重置密码。
- org_admin 登录时限制可选组织和角色。

验证 TODO：
- super_admin 可新增、编辑、禁用、启用、重置用户。
- org_admin 只能管理自己范围内普通用户。
- 有 OSS 账号的用户首次登录进入 OSS 绑定。
- 无 OSS 账号的用户首次登录进入首次改密。
- 服务器 curl 测试用户管理接口。
- 更新 `docs/api.md`、`docs/task-log.md`、`CHANGELOG.md`。
- 提交 GitHub。
- 服务器同步并确认后等待用户确认。

## Task 5 - 小程序首页工作台、我的页面、前后端联调
状态：DONE

目标：完成正式登录后的基础使用体验。

前端 TODO：
- 新增/调整首页工作台。
- 首页顶部显示项目名、用户姓名、所属组织、角色。
- 首页突出快捷查询入口：ONU MAC / 手机号 / OSS 账号。
- 首页从 `/api/workbench/apps` 获取菜单。
- 首页按 `group_name` 分组展示菜单。
- 不同角色看到不同菜单。
- 新增/调整我的页面。
- 我的页面显示姓名、手机号、用户类型、OSS 账号、OSS 绑定状态、所属组织、当前角色。
- org_admin 显示管理范围。
- 我的页面支持修改密码入口。
- 我的页面支持 OSS 账号确认或更新入口。
- 我的页面支持退出登录。
- 退出登录后清理 token 并返回登录页。
- 前端视觉统一为灰白蓝灰内部运维工具风格。

联调 TODO：
- 本地微信开发者工具调试小程序。
- 后端使用服务器接口。
- 跑通登录、获取个人信息、获取菜单。
- 跑通用户管理基本流程。
- 记录联调问题和修复记录。

验证 TODO：
- normal_user 登录后只看到普通菜单。
- org_admin 登录后可看到用户管理。
- super_admin 登录后可看到组织管理、菜单管理、系统设置。
- 我的页面信息准确。
- 退出登录行为正确。
- 更新 `docs/task-log.md`、`CHANGELOG.md`。
- 提交 GitHub。
- 服务器代码保持与 GitHub 一致。
- 输出最终测试记录。

## 执行规则
- 每个 Task 完成后必须更新 `AGENTS.md`、`CHANGELOG.md` 或 `docs/task-log.md`。
- 每个 Task 完成后必须提交并推送 GitHub。
- 每个 Task 完成后服务器代码必须与 GitHub 保持一致。
- 后端测试和部署在服务器 JSCN-233 执行。
- 本地不创建后端虚拟环境，不本地安装后端依赖。
- 前端小程序只在本地微信开发者工具调试，不部署到服务器。
- 每个 Task 完成后等待用户确认，再进入下一个 Task。
