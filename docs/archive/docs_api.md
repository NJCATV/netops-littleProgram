# 本文件已归档

本文件已归档，当前项目以根目录 AGENTS.md 和《统一工单池_含OSS融合_技术与实施总规划.md》为准。

# API 文档

## 统一响应

成功：
```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

失败：
```json
{
  "code": 4001,
  "message": "错误说明",
  "data": null
}
```

## 健康检查

### GET /api/health
返回后端进程状态。

响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "status": "healthy"
  }
}
```

## 登录认证

认证接口统一使用 JSON 请求体。除登录接口外，均需携带请求头：

```http
Authorization: Bearer <access_token>
```

### POST /api/auth/login
支持手机号或 OSS 账号登录，密码为本系统密码。

请求：
```json
{
  "account": "13100000000",
  "password": "12345678"
}
```

响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "<jwt>",
    "token_type": "Bearer",
    "next_action": "bind_oss",
    "user": {
      "id": 1,
      "user_type": "internal",
      "real_name": "张三",
      "mobile": "13100000000",
      "oss_account": "oss001",
      "oss_bind_status": "pending",
      "org_id": 1,
      "org_name": "南京",
      "role_code": "normal_user",
      "manage_org_id": null,
      "manage_org_name": null,
      "status": "active",
      "password_status": "initial"
    }
  }
}
```

`next_action` 取值：
- `bind_oss`：初始密码用户且存在 OSS 账号，需要先确认绑定。
- `change_password`：初始密码用户无 OSS 账号，直接进入首次改密。
- `home`：可进入工作台。

登录成功或失败会写入 `login_logs`。

### GET /api/auth/me
返回当前登录用户信息和下一步动作。

响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "user": {},
    "next_action": "home"
  }
}
```

### POST /api/auth/bind-oss
校验 OSS 账号密码，成功后加密保存 OSS 密码并更新绑定状态。

请求：
```json
{
  "oss_account": "oss001",
  "oss_password": "oss-password"
}
```

响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "next_action": "change_password",
    "user": {}
  }
}
```

绑定成功或失败会写入 `operation_logs`。

### POST /api/auth/change-password
修改当前用户密码，成功后 `password_status` 更新为 `normal`。

请求：
```json
{
  "old_password": "12345678",
  "new_password": "new-password"
}
```

响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "next_action": "home",
    "user": {}
  }
}
```

改密成功会写入 `operation_logs`。

### POST /api/auth/logout
JWT 当前为无状态令牌，退出接口返回成功，客户端负责清理本地 token。

响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "logged_out": true
  }
}
```

## 工作台

### GET /api/workbench/apps
按当前用户角色和用户类型返回可见功能菜单。

响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [],
    "groups": [
      {
        "group_name": "我的常用",
        "items": []
      }
    ]
  }
}
```

## 组织管理

组织管理接口均需登录。`super_admin` 可维护全部组织；`org_admin` 可查看管理范围内组织树。

- `GET /api/admin/orgs/tree`：组织树和扁平组织列表。
- `POST /api/admin/orgs`：新增组织，仅 `super_admin`。
- `PUT /api/admin/orgs/{id}`：编辑组织名称和排序。
- `POST /api/admin/orgs/{id}/disable`：禁用组织，仅 `super_admin`。

组织固定三层，新增下级时后端会校验层级不能超过 3。

## 功能菜单管理

功能菜单管理接口均需登录且仅 `super_admin` 可访问。

- `GET /api/admin/menus`：菜单列表。
- `POST /api/admin/menus`：新增菜单。
- `PUT /api/admin/menus/{id}`：编辑菜单。
- `POST /api/admin/menus/{id}/enable`：启用菜单。
- `POST /api/admin/menus/{id}/disable`：停用菜单。

菜单字段包括：
- `menu_key`：唯一标识。
- `name`：功能名称。
- `icon`：小程序图标名。
- `path`：页面路径，空值表示功能开发中。
- `group_name`：分组名，例如 `我的常用`、`全部功能`、`管理工具`。
- `min_role`：最低可见角色，`normal_user`、`org_admin`、`super_admin`。
- `user_type`：可见用户类型，`internal`、`external`、`system`、`all`。
- `enabled`：是否启用。
- `sort_order`：排序。

## 用户管理

用户管理接口均需登录。`super_admin` 可管理全部用户；`org_admin` 只能管理 `manage_org_id` 及下级组织内的 `internal + normal_user`。

- `GET /api/admin/users`：用户列表，支持 `keyword`、`org_id`、`role_code`、`status`、`oss_bind_status`、`user_type`、`page`、`page_size`。
- `GET /api/admin/users/options`：组织、角色、状态、OSS 绑定状态等选项。
- `POST /api/admin/users`：新增用户。
- `PUT /api/admin/users/{id}`：编辑用户。
- `POST /api/admin/users/{id}/disable`：禁用用户。
- `POST /api/admin/users/{id}/enable`：启用用户。
- `POST /api/admin/users/{id}/reset-password`：重置密码。

新增和重置用户初始密码为手机号后四位加 `@jscn`。有 OSS 账号时 `oss_bind_status=pending`，无 OSS 账号时 `oss_bind_status=unbound`。
