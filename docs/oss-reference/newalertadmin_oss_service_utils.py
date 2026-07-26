"""
通用的 OSS Service 工具：
- call_with_token_refresh：封装一次调用，检测 token 失效则自动重登并刷新缓存，然后重试一次。
"""
from typing import Callable, Dict, Any
import json
from app.logger import oss_client_service_logger
from tools.log_user import log_integration_audit
from app.databases.connection_manager import ConnectionManager
from app.databases.newainew_models import OssAccount
from tools.res_aes_cipher import ResAESCipher
from app.config import (
    OSS_ACCOUNT_AES_KEY, OSS_ACCOUNT_AES_IV,
    OSS_PASSWORD_AES_KEY, OSS_PASSWORD_AES_IV,
)
from app.services.oss_login_service import oss_login_and_cache
from tools.oss_api_client import OSSClient


def _get_plain_oss_credentials(local_user_id: int):
    """从 DB 读取该本地用户绑定的 OSS 账号与加密密码，并解密为明文。"""
    with ConnectionManager.get_session('newAInew') as sess:
        acc = sess.query(OssAccount).filter_by(user_id=local_user_id).first()
        if not acc:
            return None, None
        account_cipher = ResAESCipher(OSS_ACCOUNT_AES_KEY, OSS_ACCOUNT_AES_IV)
        password_cipher = ResAESCipher(OSS_PASSWORD_AES_KEY, OSS_PASSWORD_AES_IV)
        try:
            username = account_cipher.decrypt(acc.oss_account)
            password = password_cipher.decrypt(acc.password_hash)
            return username, password
        except Exception as e:
            oss_client_service_logger.error(f"解密OSS账号失败 user_id={local_user_id} error={e}")
            return None, None


def _need_refresh_token(result: Dict[str, Any]) -> bool:
    """根据返回判断是否需要刷新token。"""
    if not isinstance(result, dict):
        return False
    code = str(result.get('returnCode')) if result.get('returnCode') is not None else ''
    info = (result.get('resultInfo') or '').lower()
    http_status = result.get('http_status')
    markers = ['token失效', 'unauthorized', 'invalid token', 'token invalid', 'oss用户信息不存在', 'oss_info不存在']
    return (
        ('-1' == code and any(m in info for m in markers)) or
        http_status in (401, 403) or
        code == '-3'  # 本地判定token不存在
        or code == '-7'  # 本地判定oss_info缺失，需刷新
    )


def call_with_token_refresh(local_user_id: int, action: str, call_once: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    """
    执行一次调用，如果发现token失效/不存在，则：
    1. 自动读取本地绑定的OSS账号密码并重登，刷新redis中的token与info；
    2. 然后重试调用一次；
    若重登失败，则返回登录失败的结果。
    """
    # 第一次尝试
    oss_client_service_logger.debug(f"{action} 第一次调用 userId={local_user_id}")
    result = call_once()
    if not _need_refresh_token(result):
        return result

    oss_client_service_logger.info(f"{action} 触发自动重登 userId={local_user_id} code={result.get('returnCode')} info={result.get('resultInfo')}")
    # 自动重登
    username, password = _get_plain_oss_credentials(local_user_id)
    if not username or not password:
        fail = {
            'returnCode': '-5',
            'resultInfo': '未找到绑定的OSS账号或密文损坏，无法自动重登',
            'responseBody': '',
            'http_status': None
        }
        log_integration_audit(local_user_id, f'{action}_auto_relogin', 'failed', str(fail))
        return fail

    login_res = oss_login_and_cache(username, password, local_user_id)
    if str(login_res.get('returnCode')) != '0':
        # 登录失败，返回登录失败信息
        log_integration_audit(local_user_id, f'{action}_auto_relogin', 'failed', str(login_res))
        return login_res

    log_integration_audit(local_user_id, f'{action}_auto_relogin', 'success', 'auto relogin ok')
    # 第二次重试
    oss_client_service_logger.debug(f"{action} 重登后第二次调用 userId={local_user_id}")
    return call_once()


def with_auto_refresh(local_user_id: int, action: str, do_call: Callable[[str, Dict[str, Any]], Dict[str, Any]], *, require_info: bool = True) -> Dict[str, Any]:
    """
    进一步封装：统一“读取token/info -> 调用 -> 自动刷新”的流程。
    do_call 接收 (token, info) 两个参数，返回 OSS 接口结果 dict。
    require_info=True 时，如果 info 缺失则触发自动重登刷新。
    """
    client = OSSClient()

    def _once() -> Dict[str, Any]:
        oss_client_service_logger.debug(f"{action} 读取token及用户信息 userId={local_user_id}")
        tok = client.redis.get(f"oss_token:{local_user_id}")
        if hasattr(tok, 'decode'):
            tok = tok.decode()
        if not tok:
            return {'returnCode': '-3', 'resultInfo': 'OSS token不存在', 'responseBody': '', 'http_status': None}

        info = None
        if require_info:
            raw = client.redis.get(f"oss_info:{local_user_id}")
            if not raw:
                return {'returnCode': '-7', 'resultInfo': 'OSS用户信息不存在', 'responseBody': '', 'http_status': None}
            try:
                info = json.loads(raw)
            except Exception:
                return {'returnCode': '-7', 'resultInfo': 'OSS用户信息不存在', 'responseBody': '', 'http_status': None}

        return do_call(tok, info)

    return call_with_token_refresh(local_user_id, action, _once)
