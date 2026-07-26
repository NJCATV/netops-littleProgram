
import json
from app.logger import oss_client_service_logger
from tools.oss_api_client import OSSClient
from tools.log_user import log_integration_audit
from app.extensions import db
from app.databases.connection_manager import ConnectionManager
from app.databases.newainew_models import OssAccount
from tools.res_aes_cipher import ResAESCipher
from app.config import (
    OSS_ACCOUNT_AES_KEY, OSS_ACCOUNT_AES_IV,
    OSS_PASSWORD_AES_KEY, OSS_PASSWORD_AES_IV,
)


def oss_login_and_cache(username: str, password: str, local_user_id: int, redis_expire: int = 3600) -> dict:
    """
    调用OSSClient.login，解析token和用户信息并写入redis。
    支持本地用户id和OSS id绑定，均存入redis。
    返回原始登录结果。
    """
    client = OSSClient()
    oss_client_service_logger.info(f"开始OSS登录 username={username} localUserId={local_user_id} 过期秒={redis_expire}")
    result = client.login(username, password, user_id=local_user_id)
    oss_client_service_logger.debug(f"登录返回代码={result.get('returnCode')} http状态={result.get('http_status')} 是否含token={bool(result.get('token'))}")
    # 只有登录成功才写入redis
    if result.get('returnCode') == '0' and local_user_id:
        token = result.get('token')
        # if token and isinstance(token, str) and token.startswith('Bearer '):
        #     token = token[7:]
        response_body = result.get('responseBody')
        if token:
            try:
                client.redis.set(f"oss_token:{local_user_id}", token, ex=redis_expire)
                oss_client_service_logger.info(f"缓存token成功 user={local_user_id} token长度={len(token) if isinstance(token,str) else 'NA'}")
            except Exception as e:
                oss_client_service_logger.error(f"缓存token失败 user={local_user_id} error={e}")
        if response_body:
            try:
                if isinstance(response_body, dict):
                    client.redis.set(f"oss_info:{local_user_id}", json.dumps(response_body, ensure_ascii=False), ex=redis_expire)
                else:
                    client.redis.set(f"oss_info:{local_user_id}", str(response_body), ex=redis_expire)
                oss_client_service_logger.info(f"缓存用户信息成功 user={local_user_id}")
            except Exception as e:
                oss_client_service_logger.error(f"缓存用户信息失败 user={local_user_id} error={e}")
        # 写入数据库日志
        log_integration_audit(
            user_id=local_user_id,
            action='oss_login',
            status='success',
            response=json.dumps(result, ensure_ascii=False)
        )
    else:
        try:
            _snippet = json.dumps(result, ensure_ascii=False)
            if len(_snippet) > 400:
                _snippet = _snippet[:400] + '...truncated'
        except Exception:
            _snippet = str(result)
        oss_client_service_logger.warning(f"OSS登录失败 username={username} user={local_user_id} 响应片段={_snippet}")
        # 写入数据库日志（失败）
        log_integration_audit(
            user_id=local_user_id,
            action='oss_login',
            status='failed',
            response=json.dumps(result, ensure_ascii=False)
        )
    return result

def get_oss_user_info_by_id(user_id: str):
    """
    根据 OSS 用户id，从 redis 读取用户信息（JSON 字符串转为 dict）。
    若 token 或用户信息缺失，将尝试自动刷新后重试一次。
    返回解析后的精简 dict；失败时返回 None 或原始字符串（兼容旧逻辑）。
    """
    client = OSSClient()
    oss_client_service_logger.info(f"读取OSS用户信息 userId={user_id}")

    def _read_info():
        info = client.redis.get(f"oss_info:{user_id}")
        if not info:
            return None, None
        try:
            data = json.loads(info)
            return data, None
        except Exception as e:
            return None, info

    def _parse_and_log(data: dict):
        parsed = {
            'oss_username': data.get('sysUserName'),
            'oss_staff_name': data.get('staffName'),
            'oss_staff_id': data.get('staffId'),
            'oss_user_id': data.get('sysUserId'),
            'dept_name': data.get('deptName'),
            'area_name': data.get('areaName'),
            'work_area_id': data.get('workAreaId'),
            'work_area_name': data.get('workAreaName'),
            'work_area_names': data.get('workAreaNames'),
            'work_area_ids': data.get('workAreaIds'),
            'is_audit': data.get('isAudit'),
            'admin_flag': data.get('adminFlag'),
            'monitor_flag': data.get('monitorFlag'),
            'speer_flag': data.get('speerFlag'),
            'speer_monitor_flag': data.get('speerMonitorFlag'),
            'work_mode': data.get('workMode'),
            'area_id': data.get('areaId'),
            'local_net_id': data.get('localNetId'),
        }
        log_integration_audit(user_id=user_id, action='oss_user_info', status='success', response=json.dumps(parsed, ensure_ascii=False))
        return parsed

    data, raw = _read_info()
    if data is not None:
        oss_client_service_logger.info(f"OSS用户信息解析成功 userId={user_id}")
        return _parse_and_log(data)

    # 缺失或解析失败 -> 自动刷新一次
    try:
        uid_int = int(user_id)
    except Exception:
        uid_int = None

    if uid_int is not None:
        with ConnectionManager.get_session('newAInew') as sess:
            acc = sess.query(OssAccount).filter_by(user_id=uid_int).first()
            if acc:
                account_cipher = ResAESCipher(OSS_ACCOUNT_AES_KEY, OSS_ACCOUNT_AES_IV)
                password_cipher = ResAESCipher(OSS_PASSWORD_AES_KEY, OSS_PASSWORD_AES_IV)
                try:
                    username = account_cipher.decrypt(acc.oss_account)
                    password = password_cipher.decrypt(acc.password_hash)
                    oss_client_service_logger.info(f"用户信息缺失触发自动登录刷新 userId={user_id}")
                    login_res = oss_login_and_cache(username, password, local_user_id=uid_int)
                    if str(login_res.get('returnCode')) != '0':
                        oss_client_service_logger.warning(f"自动刷新登录失败 userId={user_id} code={login_res.get('returnCode')}")
                    else:
                        oss_client_service_logger.info(f"自动刷新登录成功 userId={user_id}")
                except Exception as e:
                    oss_client_service_logger.error(f"自动刷新解密或登录异常 userId={user_id} error={e}")

    # 刷新后再读一次
    data, raw = _read_info()
    if data is not None:
        oss_client_service_logger.info(f"OSS用户信息解析成功(刷新后) userId={user_id}")
        return _parse_and_log(data)

    # 仍失败：按旧逻辑返回 raw 或 None
    raw_str = ''
    if raw is not None:
        try:
            raw_str = raw.decode() if hasattr(raw, 'decode') else str(raw)
        except Exception:
            raw_str = str(raw)
    oss_client_service_logger.warning(f"OSS用户信息最终失败 userId={user_id} 原始长度={len(raw_str)}")
    log_integration_audit(user_id=user_id, action='oss_user_info', status='failed', response=raw_str)
    return None if not raw_str else raw_str

# 示例用法：
if __name__ == '__main__':
    username = '<oss-username>'
    password = '<oss-password>'
    res = oss_login_and_cache(username, password,1111)
    print(res)
