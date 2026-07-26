import json

import redis
import requests

from app.config import OSS_BASE_URL, OSS_REDIS_URL
from app.logger import oss_api_client_logger


class OSSClient:


    def __init__(self):
        self.base_url = OSS_BASE_URL.rstrip('/')
        self.redis = redis.Redis.from_url(OSS_REDIS_URL)

    def login(self, username: str, password: str, user_id: int = None) -> dict:
        """
        登录 OSS：明文密码在客户端 MD5 后，以“伪 JSON 字符串”发起
        """
        from tools.md5_js import md5_js
        url = f"{self.base_url}/login"
        md5_pwd = md5_js(password)

        # 注意：登录接口要的就是单引号的字符串
        body = f"{{'passWord':'{md5_pwd}','userName':'{username}','comeFrom':'2'}}"
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        try:
            oss_api_client_logger.info(f"[OSS] 准备请求 /login，发送 Body: {body}")
            resp = requests.post(url, data=body, headers=headers, timeout=10)
            try:
                result = resp.json()
            except Exception:
                result = {'returnCode': '-1', 'resultInfo': 'OSS接口返回非JSON', 'responseBody': resp.text}
            token = resp.headers.get('Authorization')
            result['token'] = token
            result['http_status'] = resp.status_code
            return result
        except requests.RequestException as e:
            return {
                'returnCode': '-2',
                'resultInfo': f'OSS接口请求异常: {str(e)}',
                'responseBody': '',
                'token': None,
                'http_status': None
            }

    def query_todo_sheet(self, token: str, body: dict) -> dict:
        """
        查询待办工单：
        - 该接口要的是【raw 文本里的 JSON 字符串（双引号）】
        - Header 仍要求 Content-Type 为 x-www-form-urlencoded; charset=UTF-8
        """
        url = f"{self.base_url}/TODO_SHEET_QUERY"

        # 1) 处理 token：兼容裸 token / 已带 Bearer 的情况
        if token and not token.lower().startswith("bearer "):
            token = f"Bearer {token}"

        # 2) 字段名修正 + 值规范化（列表转逗号字符串，只保留必要字段）
        payload = {}
        for k, v in (body or {}).items():
            if v is None:
                continue
            key = 'workAreaId' if k == 'workAreaIds' else k  # 统一成单数键
            if isinstance(v, (list, tuple)):
                payload[key] = ",".join(map(str, v))
            else:
                payload[key] = str(v)

        # 只发最小必要字段，避免触发后端“解密”分支
        # 调整：允许 staffId，下游 picked 查询不再需要 isAll / searchStaffId
        minimal_keys = [
            'workAreaId', 'localNetId', 'areaId', 'runSts', 'actTypes', 'staffId',
            'rp', 'page', 'beginTime', 'endTime'
        ]
        payload = {k: v for k, v in payload.items() if k in minimal_keys and v != ''}

        # 3) 生成“raw 文本 JSON”，注意双引号
        raw_text = json.dumps(payload, ensure_ascii=False)

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Authorization": token,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }

        try:
            oss_api_client_logger.info(f"[OSS] 准备请求 /TODO_SHEET_QUERY，发送 Body: {raw_text}")
            # 注意：data 发 raw 文本（不是 json=；不是 k=v&…）
            resp = requests.post(url, data=raw_text.encode("utf-8"), headers=headers, timeout=10)
            try:
                result = resp.json()
            except Exception:
                result = {'returnCode': '-1', 'resultInfo': 'OSS接口返回非JSON', 'responseBody': resp.text}
            result['http_status'] = resp.status_code
            return result
        except requests.RequestException as e:
            return {
                'returnCode': '-2',
                'resultInfo': f'OSS接口请求异常: {e}',
                'responseBody': '',
                'http_status': None
            }

    def get_staff_list(self, token: str, work_area_id) -> dict:
        """
        查询OSS员工列表接口 /GET_STAFF_LIST
        :param token: 登录获取的token（Authorization）
        :param work_area_id: 工作区域ID（str或list）
        :return: dict，接口返回内容
        """
        url = f"{self.base_url}/GET_STAFF_LIST"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Authorization': token,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
        }
        # 支持workAreaId为list
        if isinstance(work_area_id, (list, tuple)):
            work_area_id = ','.join(map(str, work_area_id))
        payload = {"workAreaId": work_area_id}
        raw_text = json.dumps(payload, ensure_ascii=False)
        try:
            oss_api_client_logger.info(f"[OSS] 准备请求 /GET_STAFF_LIST，发送 Body: {raw_text}")
            resp = requests.post(url, data=raw_text.encode("utf-8"), headers=headers, timeout=10)
            try:
                result = resp.json()
            except Exception:
                result = {'returnCode': '-1', 'resultInfo': 'OSS接口返回非JSON', 'responseBody': resp.text}
            result['http_status'] = resp.status_code
            return result
        except requests.RequestException as e:
            return {
                'returnCode': '-2',
                'resultInfo': f'OSS接口请求异常: {str(e)}',
                'responseBody': '',
                'http_status': None
            }

    def get_sheet_detail(self, token: str, body: dict) -> dict:
        """
        查询工单详细信息接口 /SHEET_DETAIL
        - Body 采用 raw JSON 文本（双引号），字段：woNbr, soNbr, localNetId, comeHis（默认 'N'）
        - Header: Content-Type 为 application/x-www-form-urlencoded; charset=UTF-8
        - Authorization: 允许裸 token，自动补 "Bearer " 前缀
        """
        url = f"{self.base_url}/SHEET_DETAIL"

        # 处理 token：兼容裸 token / 已带 Bearer 的情况
        if token and not token.lower().startswith("bearer "):
            token = f"Bearer {token}"

        payload = {}
        for k in ["woNbr", "soNbr", "localNetId", "comeHis"]:
            v = (body or {}).get(k)
            if v is None:
                continue
            payload[k] = str(v)
        if "comeHis" not in payload:
            payload["comeHis"] = "N"

        raw_text = json.dumps(payload, ensure_ascii=False)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Authorization': token,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
        }

        try:
            oss_api_client_logger.info(f"[OSS] 准备请求 /SHEET_DETAIL，发送 Body: {raw_text}")
            resp = requests.post(url, data=raw_text.encode('utf-8'), headers=headers, timeout=10)
            try:
                result = resp.json()
            except Exception:
                result = {'returnCode': '-1', 'resultInfo': 'OSS接口返回非JSON', 'responseBody': resp.text}
            result['http_status'] = resp.status_code
            return result
        except requests.RequestException as e:
            return {
                'returnCode': '-2',
                'resultInfo': f'OSS接口请求异常: {str(e)}',
                'responseBody': '',
                'http_status': None
            }

    def get_complain_list(self, token: str, body: dict) -> dict:
        """
        投诉列表查询接口 /GET_COMPLAIN_LIST
        - Body: raw JSON 文本，当前已知字段：soNbr (业务单号)
        - Content-Type: application/x-www-form-urlencoded; charset=UTF-8
        - Authorization: Bearer token（自动补前缀）
        """
        url = f"{self.base_url}/GET_COMPLAIN_LIST"
        if token and not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        payload = {}
        if body and body.get('soNbr') not in [None, '']:
            payload['soNbr'] = str(body.get('soNbr'))
        raw_text = json.dumps(payload, ensure_ascii=False)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Authorization': token,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
        }
        try:
            oss_api_client_logger.info(f"[OSS] 准备请求 /GET_COMPLAIN_LIST，发送 Body: {raw_text}")
            resp = requests.post(url, data=raw_text.encode('utf-8'), headers=headers, timeout=10)
            try:
                result = resp.json()
            except Exception:
                result = {'returnCode': '-1', 'resultInfo': 'OSS接口返回非JSON', 'responseBody': resp.text}
            result['http_status'] = resp.status_code
            return result
        except requests.RequestException as e:
            return {
                'returnCode': '-2',
                'resultInfo': f'OSS接口请求异常: {str(e)}',
                'responseBody': '',
                'http_status': None
            }

    def get_so_eqptprod(self, token: str, body: dict) -> dict:
        """
        终端信息查询接口 /SO_EQPTPROD_QUERY
        - Body: raw JSON 文本，字段：soNbr (业务单号)
        - Header: Content-Type x-www-form-urlencoded; charset=UTF-8
        - Authorization: 自动补 Bearer 前缀
        """
        url = f"{self.base_url}/SO_EQPTPROD_QUERY"
        if token and not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        payload = {}
        if body and body.get('soNbr') not in [None, '']:
            payload['soNbr'] = str(body.get('soNbr'))
        raw_text = json.dumps(payload, ensure_ascii=False)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Authorization': token,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
        }
        try:
            oss_api_client_logger.info(f"[OSS] 准备请求 /SO_EQPTPROD_QUERY，发送 Body: {raw_text}")
            resp = requests.post(url, data=raw_text.encode('utf-8'), headers=headers, timeout=10)
            try:
                result = resp.json()
            except Exception:
                result = {'returnCode': '-1', 'resultInfo': 'OSS接口返回非JSON', 'responseBody': resp.text}
            result['http_status'] = resp.status_code
            return result
        except requests.RequestException as e:
            return {
                'returnCode': '-2',
                'resultInfo': f'OSS接口请求异常: {str(e)}',
                'responseBody': '',
                'http_status': None
            }

    def get_cust_info(self, token: str, body: dict) -> dict:
        """
        用户信息查询接口 /CUST_INFO_SELECT
        - Body: raw JSON 文本，字段：custId (客户ID，可选)
        - Header: Content-Type application/x-www-form-urlencoded; charset=UTF-8
        - Authorization: 自动补 Bearer 前缀
        """
        url = f"{self.base_url}/CUST_INFO_SELECT"
        if token and not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        payload = {}
        if body and body.get('custId') not in [None, '']:
            payload['custId'] = str(body.get('custId'))
        raw_text = json.dumps(payload, ensure_ascii=False)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Authorization': token,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
        }
        try:
            oss_api_client_logger.info(f"[OSS] 准备请求 /CUST_INFO_SELECT，发送 Body: {raw_text}")
            resp = requests.post(url, data=raw_text.encode('utf-8'), headers=headers, timeout=10)
            try:
                result = resp.json()
            except Exception:
                result = {'returnCode': '-1', 'resultInfo': 'OSS接口返回非JSON', 'responseBody': resp.text}
            result['http_status'] = resp.status_code
            return result
        except requests.RequestException as e:
            return {
                'returnCode': '-2',
                'resultInfo': f'OSS接口请求异常: {str(e)}',
                'responseBody': '',
                'http_status': None
            }

    def get_accout_info(self, token: str, body: dict) -> dict:
        """
        账户信息查询接口 /GET_ACCOUT_INFO
        - Body: raw JSON 文本，字段：areaId, custId（均可选，按抓包示例常用组合）
        - Header: Content-Type application/x-www-form-urlencoded; charset=UTF-8
        - Authorization: 自动补 Bearer 前缀
        """
        url = f"{self.base_url}/GET_ACCOUT_INFO"
        if token and not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        payload = {}
        if body:
            if body.get('areaId') not in [None, '']:
                payload['areaId'] = str(body.get('areaId'))
            if body.get('custId') not in [None, '']:
                payload['custId'] = str(body.get('custId'))
        raw_text = json.dumps(payload, ensure_ascii=False)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Authorization': token,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
        }
        try:
            oss_api_client_logger.info(f"[OSS] 准备请求 /GET_ACCOUT_INFO，发送 Body: {raw_text}")
            resp = requests.post(url, data=raw_text.encode('utf-8'), headers=headers, timeout=10)
            try:
                result = resp.json()
            except Exception:
                result = {'returnCode': '-1', 'resultInfo': 'OSS接口返回非JSON', 'responseBody': resp.text}
            result['http_status'] = resp.status_code
            return result
        except requests.RequestException as e:
            return {
                'returnCode': '-2',
                'resultInfo': f'OSS接口请求异常: {str(e)}',
                'responseBody': '',
                'http_status': None
            }

    def get_pic_info(self, token: str, body: dict) -> dict:
        """
        工单图片信息查询接口 /PIC_INFO
        - Body: raw JSON 文本，字段：woNbr, soNbr（均可选，至少一个建议传）
        - Header: Content-Type application/x-www-form-urlencoded; charset=UTF-8
        - Authorization: 自动补 Bearer 前缀
        """
        url = f"{self.base_url}/PIC_INFO"
        if token and not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        payload = {}
        if body:
            if body.get('woNbr') not in [None, '']:
                payload['woNbr'] = str(body.get('woNbr'))
            if body.get('soNbr') not in [None, '']:
                payload['soNbr'] = str(body.get('soNbr'))
        raw_text = json.dumps(payload, ensure_ascii=False)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Authorization': token,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
        }
        try:
            oss_api_client_logger.info(f"[OSS] 准备请求 /PIC_INFO，发送 Body: {raw_text}")
            resp = requests.post(url, data=raw_text.encode('utf-8'), headers=headers, timeout=10)
            try:
                result = resp.json()
            except Exception:
                result = {'returnCode': '-1', 'resultInfo': 'OSS接口返回非JSON', 'responseBody': resp.text}
            result['http_status'] = resp.status_code
            return result
        except requests.RequestException as e:
            return {
                'returnCode': '-2',
                'resultInfo': f'OSS接口请求异常: {str(e)}',
                'responseBody': '',
                'http_status': None
            }

    def sheet_fetch(self, token: str, body: dict) -> dict:
        """
        工单认领接口 /SHEET_FETCH
        - Body: raw JSON 文本，字段：woNbr(必填), woStaffId(必填)
        - Header: Content-Type application/x-www-form-urlencoded; charset=UTF-8
        - Authorization: 自动补 Bearer 前缀
        """
        url = f"{self.base_url}/SHEET_FETCH"
        if token and not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        payload = {}
        if body:
            if body.get('woNbr') not in [None, '']:
                payload['woNbr'] = str(body.get('woNbr'))
            if body.get('woStaffId') not in [None, '']:
                payload['woStaffId'] = str(body.get('woStaffId'))
        raw_text = json.dumps(payload, ensure_ascii=False)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Authorization': token,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
        }
        try:
            oss_api_client_logger.info(f"[OSS] 准备请求 /SHEET_FETCH，发送 Body: {raw_text}")
            resp = requests.post(url, data=raw_text.encode('utf-8'), headers=headers, timeout=10)
            try:
                result = resp.json()
            except Exception:
                result = {'returnCode': '-1', 'resultInfo': 'OSS接口返回非JSON', 'responseBody': resp.text}
            result['http_status'] = resp.status_code
            return result
        except requests.RequestException as e:
            return {
                'returnCode': '-2',
                'resultInfo': f'OSS接口请求异常: {str(e)}',
                'responseBody': '',
                'http_status': None
            }

    def wo_return(self, token: str, body: dict) -> dict:
        """
        工单回单接口 /WO_RETURN
        Header: 与其它 OSS 接口一致 application/x-www-form-urlencoded; charset=UTF-8 + Authorization
        Body: raw JSON 文本；字段（全部由上层透传，有些可为空）：
          soNbr, woNbr, woType, failReasonId, woStaffId, soCat, returnType, remarks,
          reWorkDate, readyInstall, isSingle, chgServSpecId, isDouble, dutyCauseGrade,
          dealCode, isValidForMIIT, invalidReasonForMIIT, finishCustFdbkRslt,
          returnVisitRslt, indictSatisfaction, dissatisfiedRes, isEnterpriseAgreesmediation,
          visitFlag
        仅序列化允许字段，忽略其余；对 reWorkDate 若为 None 仍下发 null；其它字段为 None 则跳过。
        """
        url = f"{self.base_url}/WO_RETURN"
        if token and not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        allowed = [
            'soNbr','woNbr','woType','failReasonId','woStaffId','soCat','returnType','remarks',
            'reWorkDate','readyInstall','isSingle','chgServSpecId','isDouble','dutyCauseGrade',
            'dealCode','isValidForMIIT','invalidReasonForMIIT','finishCustFdbkRslt',
            'returnVisitRslt','indictSatisfaction','dissatisfiedRes','isEnterpriseAgreesmediation',
            'visitFlag'
        ]
        payload = {}
        data_src = body or {}
        oss_api_client_logger.debug(f"[OSS][WO_RETURN] 原始入参 keys={list(data_src.keys())}")
        for k in allowed:
            if k == 'reWorkDate':  # 显式下发，可为 None
                if k in data_src:
                    payload[k] = data_src.get(k)  # None -> null
                continue
            v = data_src.get(k)
            if v is not None and v != '':
                payload[k] = v
        # 基础校验
        mandatory = ['soNbr','woNbr','woStaffId']
        for m in mandatory:
            if payload.get(m) in [None, '']:
                oss_api_client_logger.warning(f"[OSS][WO_RETURN] 本地校验失败 缺失字段={m} payloadKeys={list(payload.keys())}")
                return {
                    'returnCode': '400',
                    'resultInfo': f'参数缺失: {m}',
                    'responseBody': '',
                    'http_status': None
                }
        # 记录关键字段摘要（避免日志过长）
        summary_keys = {k: payload.get(k) for k in ['woNbr','soNbr','woStaffId','woType','soCat','returnType','failReasonId'] if k in payload}
        raw_text = json.dumps(payload, ensure_ascii=False)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Authorization': token,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
        }
        try:
            oss_api_client_logger.info(f"[OSS][WO_RETURN] 发送请求 摘要={summary_keys} 全量长度={len(raw_text)}")
            # 完整请求体输出（用户明确要求完整输出）
            try:
                oss_api_client_logger.info(f"[OSS][WO_RETURN] FULL_REQUEST payload={raw_text}")
            except Exception:
                pass
            resp = requests.post(url, data=raw_text.encode('utf-8'), headers=headers, timeout=15)
            try:
                result = resp.json()
            except Exception:
                result = {'returnCode': '-1', 'resultInfo': 'OSS接口返回非JSON', 'responseBody': resp.text}
            result['http_status'] = resp.status_code
            # 仅截取前 400 字节日志
            try:
                body_snippet = json.dumps(result, ensure_ascii=False)
                if len(body_snippet) > 400:
                    body_snippet = body_snippet[:400] + '...truncated'
                oss_api_client_logger.info(f"[OSS][WO_RETURN] 响应 http_status={resp.status_code} returnCode={result.get('returnCode')} 摘要={body_snippet}")
                # 完整响应体输出
                try:
                    oss_api_client_logger.info(f"[OSS][WO_RETURN] FULL_RESPONSE http_status={resp.status_code} body={json.dumps(result, ensure_ascii=False)}")
                except Exception:
                    pass
            except Exception:
                pass
            return result
        except requests.RequestException as e:
            oss_api_client_logger.error(f"[OSS][WO_RETURN] 请求异常: {e}")
            return {
                'returnCode': '-2',
                'resultInfo': f'OSS接口请求异常: {str(e)}',
                'responseBody': '',
                'http_status': None
            }

    def fail_reason_query(self, token: str, step_id: str = "SP0015", system_name: str = "CRM", so_cat: str = "1") -> dict:
        """失败原因查询接口 /FAIL_REASON_QUERY

        - 固定 payload 字段: stepId, systemName, soCat，可接受覆盖（默认分别为 SP0015 / CRM / 1）
        - Header 与其他接口一致；Authorization 自动补 Bearer。
        """
        url = f"{self.base_url}/FAIL_REASON_QUERY"
        if token and not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        payload = {
            'stepId': step_id or 'SP0015',
            'systemName': system_name or 'CRM',
            'soCat': so_cat or '1'
        }
        raw_text = json.dumps(payload, ensure_ascii=False)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Authorization': token,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
        }
        try:
            oss_api_client_logger.info(f"[OSS] 准备请求 /FAIL_REASON_QUERY，发送 Body: {raw_text}")
            resp = requests.post(url, data=raw_text.encode('utf-8'), headers=headers, timeout=10)
            try:
                result = resp.json()
            except Exception:
                result = {'returnCode': '-1', 'resultInfo': 'OSS接口返回非JSON', 'responseBody': resp.text}
            result['http_status'] = resp.status_code
            return result
        except requests.RequestException as e:
            return {
                'returnCode': '-2',
                'resultInfo': f'OSS接口请求异常: {str(e)}',
                'responseBody': '',
                'http_status': None
            }
