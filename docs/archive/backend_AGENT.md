# 本文件已归档

本文件已归档，当前项目以根目录 AGENTS.md 和《统一工单池_含OSS融合_技术与实施总规划.md》为准。

# Backend Agent Notes

This backend directory is reserved for the Flask service of 江苏有线南京分公司智维助手.

Sensitive values from previous operational notes have been moved out of the tracked file expectation. Use `backend/.env` on local machines and the server for real passwords and secret keys. Keep only examples in `backend/.env.example`.

Current planned API deployment entry:

- Server: JSCN-233
- User: yvesyuan
- API prefix behind Nginx: `/wx/api/`
- Local Flask port: `7001`
- Database: MySQL `anbo_wx` on port `6603`

Detailed project-level instructions are maintained in root `AGENTS.md`.

## OSS Interface Notes

Base URL:

- `http://oss.js96296.com:7016/OSS-mobile/webservice/commonRs`

Known endpoints from the legacy service inventory:

| Endpoint | Method | Purpose | Notes |
| --- | --- | --- | --- |
| `/login` | POST | OSS login | Uses `userName`, MD5 `passWord`, `comeFrom=2`; response header contains `Authorization`. |
| `/TODO_SHEET_QUERY` | POST | Work order list query | Used for pending and claimed work orders. |
| `/GET_STAFF_LIST` | POST | Staff list query | Uses `workAreaId`. |
| `/SHEET_DETAIL` | POST | Work order detail query | Uses `woNbr`, `soNbr`, `localNetId`, `comeHis`. |
| `/GET_COMPLAIN_LIST` | POST | Complaint list query | Uses `soNbr`. |
| `/SO_EQPTPROD_QUERY` | POST | Terminal/device product info query | Uses `soNbr`. |
| `/CUST_INFO_SELECT` | POST | Customer info query | Uses `custId`. |
| `/GET_ACCOUT_INFO` | POST | Account info query | Uses `areaId`, `custId`; endpoint spelling is `ACCOUT`. |
| `/PIC_INFO` | POST | Work order image/attachment query | Uses `woNbr`, `soNbr`. |
| `/SHEET_FETCH` | POST | Claim work order | Uses `woNbr`, `woStaffId`. |
| `/WO_RETURN` | POST | Work order return/close | Uses fields including `soNbr`, `woNbr`, `woType`, `failReasonId`, `woStaffId`, `soCat`, `returnType`, `remarks`. |
| `/FAIL_REASON_QUERY` | POST | Failure reason query | Default legacy values included `SP0015`, `CRM`, `1`. |

Keep OSS account passwords encrypted in the database. Do not write OSS passwords or server passwords into tracked files.
