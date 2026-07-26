# newalertadmin OSS 接口参考

本目录归档服务器 `/home/yvesyuan/PycharmProjects/newalertadmin` 中已调通的 OSS 调用代码，后续本项目对接 OSS 时以这些文件为准，尽量保持请求格式一致。

## 原始代码文件

- `newalertadmin_oss_api_client.py`：OSSClient 原始实现，包含全部已调通 OSS HTTP 调用。
- `newalertadmin_oss_login_service.py`：OSS 登录、token 和用户信息缓存逻辑。
- `newalertadmin_oss_service_utils.py`：token/info 读取、自动重登和重试封装。

## 全局约定

- `OSS_BASE_URL`：`http://oss.js96296.com:7016/OSS-mobile/webservice/commonRs`
- 登录成功返回头：`Authorization`
- 业务接口 token：裸 token 需补成 `Bearer <token>`
- 业务接口通用 header：

```python
{
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Authorization": token,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Cache-Control": "no-cache",
}
```

## 当前项目接入状态

- 已接入：`backend/app/services/oss_service.py` 使用本文件记录的 `/login` 格式进行 OSS 账号密码校验。
- 已暴露：`POST /api/auth/bind-oss` 用于小程序用户主动绑定或更新 OSS 账号。
- 已调整：OSS 绑定不是进入小程序的强制步骤；未绑定用户允许进入系统，前端每次重新打开小程序后提醒一次。
- 尚未完成：OSS 工单查询、OSS 工单详情、OSS 工单同步入统一工单池、token 缓存和自动重登适配器。
- 验证口径：旧项目文件记录为已调通；当前项目代码已按该格式实现。没有真实 OSS 测试账号时，只能完成代码路径和构建验证，不能确认线上 OSS 凭据登录结果。

## 已调通接口清单

### login

- 方法：`OSSClient.login(username, password, user_id=None)`
- 路径：`POST /login`
- 关键点：明文密码先做小写 32 位 MD5；请求体不是表单键值对，而是单引号伪 JSON 字符串。

```python
md5_pwd = md5_js(password)
body = f"{{'passWord':'{md5_pwd}','userName':'{username}','comeFrom':'2'}}"
headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
resp = requests.post(url, data=body, headers=headers, timeout=10)
```

### TODO_SHEET_QUERY

- 方法：`query_todo_sheet(token, body)`
- 路径：`POST /TODO_SHEET_QUERY`
- 请求体：raw JSON 文本，双引号 JSON，`data=raw_text.encode("utf-8")`
- 字段处理：`workAreaIds` 改为 `workAreaId`；列表转逗号字符串；只保留 `workAreaId/localNetId/areaId/runSts/actTypes/staffId/rp/page/beginTime/endTime`

### GET_STAFF_LIST

- 方法：`get_staff_list(token, work_area_id)`
- 路径：`POST /GET_STAFF_LIST`
- 请求体：`{"workAreaId": work_area_id}`，`work_area_id` 可为列表，列表转逗号字符串。

### SHEET_DETAIL

- 方法：`get_sheet_detail(token, body)`
- 路径：`POST /SHEET_DETAIL`
- 请求体字段：`woNbr`、`soNbr`、`localNetId`、`comeHis`
- 默认值：`comeHis` 缺失时补 `"N"`

### GET_COMPLAIN_LIST

- 方法：`get_complain_list(token, body)`
- 路径：`POST /GET_COMPLAIN_LIST`
- 请求体字段：`soNbr`

### SO_EQPTPROD_QUERY

- 方法：`get_so_eqptprod(token, body)`
- 路径：`POST /SO_EQPTPROD_QUERY`
- 请求体字段：`soNbr`

### CUST_INFO_SELECT

- 方法：`get_cust_info(token, body)`
- 路径：`POST /CUST_INFO_SELECT`
- 请求体字段：`custId`

### GET_ACCOUT_INFO

- 方法：`get_accout_info(token, body)`
- 路径：`POST /GET_ACCOUT_INFO`
- 请求体字段：`areaId`、`custId`
- 注意：接口名按原系统拼写为 `ACCOUT`

### PIC_INFO

- 方法：`get_pic_info(token, body)`
- 路径：`POST /PIC_INFO`
- 请求体字段：`woNbr`、`soNbr`

### SHEET_FETCH

- 方法：`sheet_fetch(token, body)`
- 路径：`POST /SHEET_FETCH`
- 请求体字段：`woNbr`、`woStaffId`

### WO_RETURN

- 方法：`wo_return(token, body)`
- 路径：`POST /WO_RETURN`
- 必填字段：`soNbr`、`woNbr`、`woStaffId`
- 允许字段：

```python
[
    'soNbr','woNbr','woType','failReasonId','woStaffId','soCat','returnType','remarks',
    'reWorkDate','readyInstall','isSingle','chgServSpecId','isDouble','dutyCauseGrade',
    'dealCode','isValidForMIIT','invalidReasonForMIIT','finishCustFdbkRslt',
    'returnVisitRslt','indictSatisfaction','dissatisfiedRes','isEnterpriseAgreesmediation',
    'visitFlag'
]
```

- 特殊点：`reWorkDate` 可显式下发 `None`，序列化后为 JSON `null`。

### FAIL_REASON_QUERY

- 方法：`fail_reason_query(token, step_id="SP0015", system_name="CRM", so_cat="1")`
- 路径：`POST /FAIL_REASON_QUERY`
- 默认请求体：

```python
{
    "stepId": "SP0015",
    "systemName": "CRM",
    "soCat": "1"
}
```

## 本项目迁移要求

- OSS 登录必须使用 `newalertadmin_oss_api_client.py` 中 `login()` 的请求体格式。
- 所有业务接口必须使用 raw JSON 文本，不使用 `json=`，不使用普通表单键值对。
- 返回非 JSON 时，不向前端透传 HTML 原文，只返回明确错误信息，并在服务端日志保留必要片段。
