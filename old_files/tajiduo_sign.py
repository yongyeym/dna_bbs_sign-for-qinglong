"""
任务名称
name: 异环·塔吉多 每日签到
定时规则
cron: 3 0 * * *
"""

import time
import requests
import traceback
import base64
import json
from urllib import parse
from typing import List
from Utility.common import common_util as util
from Utility.common.common_util import SPException
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# 获取一个随机生成的32位大写UUID4，在本次运行期间使用，用于给请求头的deviceid赋值
UUID = util.get_uuid(4, True, True)
# 从环境变量或本地ini文件获取完美世界账号和密码，登录并获取accessToken和refreshToken令牌及塔吉多社区UID，refreshToken用于刷新24小时有效期的accessToken令牌，目前暂无作用
ACCOUNT_TEL, ACCOUNT_PASSWD = util.get_config_env("tajiduo_tel", "tajiduo_passwd", section="COOKIE") if util.USE_LOCAL_COOKIE else util.get_os_env("tajiduo_tel", "tajiduo_passwd")
# 定义全局变量，用于存储accessToken和refreshToken令牌，以及塔吉多社区UID
ACCESS_TOKEN = REFRESH_TOKEN = TAJIDUO_UID = ""
# 塔吉多社区IOS版 API 的 ds 防重放签名盐值
DS_SECRET = 'pUds3dfMkl'
# 请求头通用部分
OKHTTP_UA_IOS = 'HTAssistant/123 CFNetwork/3860.700.1 Darwin/25.6.0'
OKHTTP_UA = 'okhttp/4.12.0'
APPVERSION_IOS = '1.2.5'
APPVERSION = '1.1.0'
PLATFORM_IOS = 'ios'
PLATFORM = 'android'
HEADERS_COMMON_IOS = {
        'User-Agent': OKHTTP_UA_IOS,
        'Accept-Encoding': "gzip, deflate",
        'platform': PLATFORM_IOS,
        'uid': '0',
        'Accept': "application/json, text/plain, */*",
        'Accept-Language': "zh-CN,zh-Hans;q=0.9",
        'Host': "bbs-api.tajiduo.com",
        'Connection': "Keep-Alive",
        'appversion': APPVERSION_IOS,
        'deviceid': UUID,
        'authorization': ACCESS_TOKEN,
    }
HEADERS_COMMON = {
        'User-Agent': OKHTTP_UA,
        'platform': PLATFORM,
        'uid': TAJIDUO_UID,
        'appversion': APPVERSION,
        'deviceid': UUID,
        'authorization': ACCESS_TOKEN,
    }

##################### 分割线 #####################
APP_ID = '10550'
USER_CENTER_APP_ID = '10551'
SECRET = '89155cc4e8634ec5b1b6364013b23e3e'
TYPE = '16'
DEVICETYPE = 'LGE-AN10'
DEVICENAME = 'LGE-AN10'
VERSIONCODE = '1'
AREACODEID = '1'
DEVICESYS = '12'
DEVICEMODEL = 'LGE-AN10'
SDKVERSION = '4.129.0'
BID = 'com.pwrd.htassistant'
CHANNELID = '1'
DEFAULT_GAME_ID = '1289'
REQUEST_HEADERS_BASE = {
    'platform': 'android',
    'Content-Type': 'application/x-www-form-urlencoded',
}

def generate_signature(params) -> str:
    sorted_keys = sorted(params.keys())
    values = ''.join(str(params[key]) for key in sorted_keys)
    return util.get_md5(values + SECRET)

def _aes_base64_encode(text: str) -> str:
    key = SECRET[-16:].encode('utf-8')
    padder = padding.PKCS7(128).padder()
    padded = padder.update(text.encode('utf-8')) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.ECB())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(encrypted).decode('utf-8')

def _safe_json(response, endpoint: str):
    if not response.text.strip():
        raise Exception(f'{endpoint} 返回空响应，status={response.status_code}')
    try:
        return response.json()
    except json.JSONDecodeError as ex:
        raise Exception(f'{endpoint} 返回非JSON: {response.text[:200]}') from ex

def _is_ok(resp: dict) -> bool:
    return resp.get('code') == 0

##################### 分割线 #####################

def get_ds() -> str:
    """
    生成IOS版APP的请求头 ds 参数：<秒级时间戳>,<8位随机字符串>,<MD5(ts+nonce+appversion+盐)>
    """
    ts = str(util.get_timestamp(type='s'))
    nonce = util.get_radom_string(8)
    signature = util.get_md5(ts + nonce + APPVERSION_IOS + DS_SECRET)
    return f'{ts},{nonce},{signature}'

def do_wanmei_account_login() -> tuple[str, ...]:
    """
    API：m/newApi/login
    登录完美世界账号，获取uid和token用于后续登录塔吉多社区
    """
    url = "https://user.laohu.com/m/newApi/login"
    data = {
        'deviceType': DEVICETYPE,
        'type': TYPE,
        'deviceId': UUID,
        'deviceName': DEVICENAME,
        'versionCode': VERSIONCODE,
        't': str(util.get_timestamp(type='s')),
        'areaCodeId': AREACODEID,
        'appId': APP_ID,
        'deviceSys': DEVICESYS,
        'username': ACCOUNT_TEL,
        'password': ACCOUNT_PASSWD,
        'deviceModel': DEVICEMODEL,
        'sdkVersion': SDKVERSION,
        'bid': BID,
        'channelId': CHANNELID,
    }
    data['sign'] = generate_signature(data)

    resp = _safe_json(
        requests.post(url, data=parse.urlencode(data), headers=REQUEST_HEADERS_BASE),
        '密码登录(不加密)',
    )

    if not _is_ok(resp):
        msg = str(resp.get('message') or resp.get('msg') or resp)
        if 'BAD_REQUEST' in msg:
            username_enc = _aes_base64_encode(ACCOUNT_TEL)
            login_password_enc = _aes_base64_encode(ACCOUNT_PASSWD)
            data['username'] = username_enc
            data['password'] = login_password_enc
            data['sign'] = generate_signature(data)
            resp = _safe_json(
                requests.post(url, data=parse.urlencode(data), headers=REQUEST_HEADERS_BASE),
                '密码登录(加密)',
            )

        if not _is_ok(resp):
            raise Exception(f'密码登录失败: {resp.get("message") or resp.get("msg") or resp}')

    result = resp.get('result') or {}
    token = result.get('token')
    user_id = result.get('userId')
    if not token or user_id is None:
        raise Exception(f'登录返回缺少 token/userId: {resp}')
    return token, str(user_id)

def do_usercenter_login(token: str, user_id: str):
    """
    API：usercenter/api/login
    登录塔吉多社区账号，获取用户的accessToken和refreshToken及塔吉多社区UID，更新到全局变量中
    """
    global ACCESS_TOKEN, REFRESH_TOKEN, TAJIDUO_UID
    url = "https://bbs-api.tajiduo.com/usercenter/api/login"
    headers = {
        **REQUEST_HEADERS_BASE,
        'deviceid': UUID,
        'authorization': '',
        'appversion': APPVERSION,
        'uid': '10000000',
        'User-Agent': OKHTTP_UA,
    }
    data = {
        'token': token,
        'userIdentity': user_id,
        'appId': USER_CENTER_APP_ID,
    }
    resp = _safe_json(
        requests.post(url, data=data, headers=headers),
        '用户中心登录',
    )
    if not _is_ok(resp):
        raise Exception(f'用户中心登录失败: {resp.get("msg") or resp}')
    data = resp.get('data') or {}
    if not data.get('accessToken') or not data.get('refreshToken'):
        raise Exception(f'用户中心登录返回缺少 accessToken/refreshToken: {resp}')
    ACCESS_TOKEN = data['accessToken']
    REFRESH_TOKEN = data['refreshToken']
    TAJIDUO_UID = str(data.get('uid', ''))

def do_refresh_token(refresh_token: str):
    """
    API：usercenter/api/refreshToken
    刷新用户的accessToken和refreshToken，更新到全局变量中
    此API目前无作用：因为首次登录时也会获取到accessToken，每次运行都会重新获取，无需刷新。
    """
    global ACCESS_TOKEN, REFRESH_TOKEN
    url = "https://bbs-api.tajiduo.com/usercenter/api/getUserFullInfo"
    headers = {
        **REQUEST_HEADERS_BASE,
        'deviceid': UUID,
        'authorization': refresh_token,
        'appversion': APPVERSION,
        'uid': '10000000',
        'User-Agent': OKHTTP_UA,
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 402:
        raise Exception('refreshToken 已失效，请重新获取')
    resp = _safe_json(response, '刷新token')
    if not _is_ok(resp):
        raise Exception(f'刷新token失败: {resp.get("msg") or resp}')

    data = resp.get('data') or {}
    if not data.get('accessToken') or not data.get('refreshToken'):
        raise Exception(f'刷新token返回缺少 accessToken/refreshToken: {resp}')
    ACCESS_TOKEN = data.get('accessToken')
    REFRESH_TOKEN = data.get('refreshToken')

def get_user_fullinfo():
    """
    API：usercenter/api/getUserFullInfo
    获取塔吉多社区用户的个人账号资料信息，更新塔吉多uid全局变量
    此API目前无作用：因为塔吉多UID已经从登录API获取
    """
    global TAJIDUO_UID
    url = "https://bbs-api.tajiduo.com/usercenter/api/getUserFullInfo"
    data = {}
    response = get_response(url, data, 1)
    if response["code"] == 0:
        TAJIDUO_UID = response["data"]["userStat"]["uid"]
    elif response["code"] == 401:
        # code 401 表示当前accessToken过期，需要使用refreshToken刷新两个Token，因为是刚刚获取的新令牌，出现此问题通常无法通过刷新令牌解决，直接抛出异常，让用户重新运行脚本
        raise SPException("accessToken失效", "accessToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 402:
        raise SPException("refreshToken失效", "refreshToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 500:
        raise SPException("获取用户塔吉多社区UID失败", f"获取用户塔吉多社区UID失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取用户塔吉多社区UID失败",f"获取用户塔吉多社区UID失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_tajiduo_taskprocess() -> tuple[int, ...]:
    """
    API：apihub/api/getUserTasks
    获取塔吉多社区用户的社区每日任务（task_list1）和一次性任务（task_list2）完成情况：
    :return 返回每日任务还差几次完成，like 每日点赞5次帖子、read 每日阅读3次帖子、share 每日分享1次帖子、bbs_sign 社区签到情况（1=未签到，0=已签到）
    """
    bbs_sign = like = read = share = 0
    url = "https://bbs-api.tajiduo.com/apihub/api/getUserTasks"
    data = {
        'gid': "1",  # 未知用途
    }
    response = get_response(url, data, 2)
    if response["code"] == 0:
        data = response["data"]["task_list1"]
        for i in range(len(data)):
            if data[i]['taskKey'] == "like_post_c":
                like = data[i]['limitTimes'] - data[i]['completeTimes']
            if data[i]['taskKey'] == "browse_post_c":
                read = data[i]['limitTimes'] - data[i]['completeTimes']
            if data[i]['taskKey'] == "share":
                share = data[i]['limitTimes'] - data[i]['completeTimes']
            if data[i]['taskKey'] == "signin_c":
                bbs_sign = data[i]['limitTimes'] - data[i]['completeTimes']
        return int(read), int(like), int(share), int(bbs_sign)
    elif response["code"] == 401:
        # code 401 表示当前accessToken过期，需要使用refreshToken刷新两个Token，因为是刚刚获取的新令牌，出现此问题通常无法通过刷新令牌解决，直接抛出异常，让用户重新运行脚本
        raise SPException("accessToken失效", "accessToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 402:
        raise SPException("refreshToken失效", "refreshToken失效，请尝试重新运行脚本！")
    elif response["code"] == 500:
        raise SPException("获取社区每日任务进度失败", f"获取社区每日任务进度失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取社区每日任务进度失败",f"获取社区每日任务进度失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_tajiduo_new_formlist() -> List[str]:
    """
    API：bbs/api/getColumnPostList
    获取塔吉多异环-「呗果」揭示板分版下最新发布的帖子列表
    用于获取帖子ID进行点赞和浏览的每日任务
    获取最新发布的用户水区是确保每天获取的第一页帖子列表一定是新帖子，防止对已经浏览/点赞过的帖子再次处理导致任务进度不增加
    :return 返回多个帖子的postId，默认返回5个帖子ID
    """
    url = "https://bbs-api.tajiduo.com/bbs/api/getColumnPostList"
    data = {
        'communityId': "2",  # 对应版块ID 1 幻塔 | 2 异环
        'columnId': "2",  # 对应板块分区ID 2 「呗果」揭示板 | 4 「袋先生」邮箱 | 8 「Zoomer」选辑
        'page': "1",  # 页码
        'count': "20",  # 一页内容数量
        'sortType': "1",  # 排序规则，1 最新发布 | 2 最新回复 | 3 推荐排序
        'version': "0",  # 未知用途
    }
    response = get_response(url, data, 2)
    if response["code"] == 0:
        data = response["data"]["posts"]
        postIds = lambda p, cont: [p[i]['postStat']['postId'] for i in range(cont)]  # 返回水区最新发布帖子的前多少个帖子ID，传入准备好的response指定部分json和需要的帖子id数量，返回包含指定数量id的int列表
        return postIds(data, 5)
    elif response["code"] == 401:
        # code 401 表示当前accessToken过期，需要使用refreshToken刷新两个Token，因为是刚刚获取的新令牌，出现此问题通常无法通过刷新令牌解决，直接抛出异常，让用户重新运行脚本
        raise SPException("accessToken失效", "accessToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 402:
        raise SPException("refreshToken失效", "refreshToken失效，请尝试重新运行脚本！")
    elif response["code"] == 500:
        raise SPException("获取最新帖子列表失败", f"获取最新帖子列表失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取最新帖子列表失败", f"获取最新帖子列表失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_post_detail(postId: str) -> bool:
    """
    API：bbs/api/getPostFull
    浏览帖子详情的API，用于完成每日浏览任务
    :param postId: 帖子ID
    :return 返回布尔值，True为帖子被删除需要重新执行一遍，False为正常处理
    """
    url = "https://bbs-api.tajiduo.com/bbs/api/getPostFull"
    data = {
        'postId': postId  # 帖子ID
    }
    response = get_response(url, data, 2)
    if response["code"] == 0:
        return False
    elif response["code"] == 401:
        # code 401 表示当前accessToken过期，需要使用refreshToken刷新两个Token，因为是刚刚获取的新令牌，出现此问题通常无法通过刷新令牌解决，直接抛出异常，让用户重新运行脚本
        raise SPException("accessToken失效", "accessToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 402:
        raise SPException("refreshToken失效", "refreshToken失效，请尝试重新运行脚本！")
    elif response["code"] == 501:
        return True  # 这篇帖子被删除，返回False令程序从获取新的帖子ID步骤从新开始执行
    elif response["code"] == 500:
        raise SPException("浏览帖子任务失败", f"浏览帖子任务失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("浏览帖子任务失败", f"浏览帖子任务失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_like(postId: str) -> bool:
    """
    API：bbs/api/post/like
    进行点赞的API，用于完成每日点赞任务
    为了防止传入的帖子本身是已经点过赞的，导致第一次点赞无效
    因此第一次点赞前会先调用取消点赞API确保帖子是没有点赞的状态
    :param postId: 帖子ID
    :return 返回布尔值，True为帖子被删除需要重新执行一遍，False为正常处理
    """
    url = "https://bbs-api.tajiduo.com/bbs/api/post/like"
    data = {
        'postId': postId,  # 帖子ID
    }
    response = get_response(url, data, 1)
    if response["code"] == 0:
        return False
    elif response["code"] == 401:
        # code 401 表示当前accessToken过期，需要使用refreshToken刷新两个Token，因为是刚刚获取的新令牌，出现此问题通常无法通过刷新令牌解决，直接抛出异常，让用户重新运行脚本
        raise SPException("accessToken失效", "accessToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 402:
        raise SPException("refreshToken失效", "refreshToken失效，请尝试重新运行脚本！")
    elif response["code"] == 501:
        return True  # 这篇帖子被删除，返回False令程序从获取新的帖子ID步骤从新开始执行
    elif response["code"] == 500:
        raise SPException("社区点赞任务失败", f"社区点赞任务失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("社区点赞任务失败", f"社区点赞任务失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_unlike(postId: str) -> bool:
    """
    API：bbs/api/post/unlike
    进行取消点赞的API，目前不会使用到
    :param postId: 帖子ID
    :return 返回布尔值，True为帖子被删除需要重新执行一遍，False为正常处理
    """
    url = "https://bbs-api.tajiduo.com/bbs/api/post/unlike"
    data = {
        'postId': postId,  # 帖子ID
    }
    response = get_response(url, data, 1)
    if response["code"] == 0:
        return False
    elif response["code"] == 401:
        # code 401 表示当前accessToken过期，需要使用refreshToken刷新两个Token，因为是刚刚获取的新令牌，出现此问题通常无法通过刷新令牌解决，直接抛出异常，让用户重新运行脚本
        raise SPException("accessToken失效", "accessToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 402:
        raise SPException("refreshToken失效", "refreshToken失效，请尝试重新运行脚本！")
    elif response["code"] == 501:
        return True  # 这篇帖子被删除，返回False令程序从获取新的帖子ID步骤从新开始执行
    elif response["code"] == 500:
        raise SPException("社区点赞任务失败", f"社区点赞任务失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("社区点赞任务失败", f"社区点赞任务失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_share(postId: str) -> bool:
    """
    API：bbs/api/post/share
    进行分享任务进度提交的API
    :param postId: 帖子ID
    :return 返回布尔值，True为帖子被删除需要重新执行一遍，False为正常处理
    """
    url = "https://bbs-api.tajiduo.com/bbs/api/post/share"
    data = {
        'platform': "wx_session",  # 分享平台，微信渠道
        'postId': postId  # 帖子ID
    }
    response = get_response(url, data, 1)
    if response["code"] == 0:
        return False
    elif response["code"] == 401:
        # code 401 表示当前accessToken过期，需要使用refreshToken刷新两个Token，因为是刚刚获取的新令牌，出现此问题通常无法通过刷新令牌解决，直接抛出异常，让用户重新运行脚本
        raise SPException("accessToken失效", "accessToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 402:
        raise SPException("refreshToken失效", "refreshToken失效，请尝试重新运行脚本！")
    elif response["code"] == 501:
        return True  # 这篇帖子被删除，返回False令程序从获取新的帖子ID步骤从新开始执行
    elif response["code"] == 500:
        raise SPException("社区分享任务失败", f"社区分享任务失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("社区分享任务失败", f"社区分享任务失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_signin_bbs() -> str:
    """
    API：apihub/api/signin
    进行塔吉多签到的API
    :return message: 社区签到执行相关的文本日志
    """
    message = ""
    url = "https://bbs-api.tajiduo.com/apihub/api/signin"
    data = {
        'communityId': "2"  # 对应ID 2 异环版区
    }
    response = get_response(url, data, 1)
    if response["code"] == 0:
        response_data = response["data"]
        message += f"塔吉多社区签到成功：今天的签到奖励是「异环版区经验」*{response_data['exp']}、「塔塔币」*{response_data['goldCoin']}。"
        return message
    elif response["code"] == 401:
        # code 401 表示当前accessToken过期，需要使用refreshToken刷新两个Token，因为是刚刚获取的新令牌，出现此问题通常无法通过刷新令牌解决，直接抛出异常，让用户重新运行脚本
        raise SPException("accessToken失效", "accessToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 402:
        raise SPException("refreshToken失效", "refreshToken失效，请尝试重新运行脚本！")
    elif response["code"] == 1551:
        message += "塔吉多社区今天已经签到过了，无需签到。"
        return message
    elif response["code"] == 500:
        raise SPException("塔吉多签到失败", f"塔吉多签到失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("塔吉多签到失败", f"塔吉多签到失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_signin_game() -> tuple[int, int]:
    """
    API：apihub/awapi/signin/state
    查询今天游戏是否已经签到，并返回当天游戏签到的奖励详情
    :return game_sign: 今天是否已经签到，1=未签到，0=已签到
    :return signin_time: 当月签到天数（包含今天）
    """
    url = "https://bbs-api.tajiduo.com/apihub/awapi/signin/state"
    data = {
        'gameId': "1289",  # 对应ID 1289=异环
    }
    response = get_response(url, data, 2)
    if response["code"] == 0:
        game_sign = 0 if response["data"]["todaySign"] else 1  # 今天是否已经签到，1=未签到，0=已签到
        signin_time = response["data"]["days"]  # 当月签到天数，获取到的原始数据，若今天未签到，则此值不包含今天
        if game_sign == 1:
            signin_time = signin_time + 1  # 今天未签到，总签到天数+1天再返回数据
        return game_sign, signin_time
    elif response["code"] == 401:
        # code 401 表示当前accessToken过期，需要使用refreshToken刷新两个Token，因为是刚刚获取的新令牌，出现此问题通常无法通过刷新令牌解决，直接抛出异常，让用户重新运行脚本
        raise SPException("accessToken失效", "accessToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 402:
        raise SPException("refreshToken失效", "refreshToken失效，请尝试重新运行脚本！")
    elif response["code"] == 500:
        raise SPException("获取游戏签到进度失败", f"获取游戏签到进度失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取游戏签到进度失败", f"获取游戏签到进度失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_signin_game_awards_list(roleId: str) -> str:
    """
    API：apihub/awapi/sign/rewards
    返回当天游戏签到的奖励详情
    :return award: 今天的游戏签到奖励
    """
    url = "https://bbs-api.tajiduo.com/apihub/awapi/sign/rewards"
    data = {
        'gameId': "1289",  # 对应ID 1289=异环
        'roleId': roleId,  # 游戏角色UID
    }
    response = get_response(url, data, 2)
    if response["code"] == 0:
        return f"「{response['data']['signin_time']['name']}」*{response['data']['signin_time']['num']}"
    elif response["code"] == 401:
        # code 401 表示当前accessToken过期，需要使用refreshToken刷新两个Token，因为是刚刚获取的新令牌，出现此问题通常无法通过刷新令牌解决，直接抛出异常，让用户重新运行脚本
        raise SPException("accessToken失效", "accessToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 402:
        raise SPException("refreshToken失效", "refreshToken失效，请尝试重新运行脚本！")
    elif response["code"] == 500:
        raise SPException("获取游戏签到奖励失败", f"获取游戏签到奖励失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取游戏签到奖励失败", f"获取游戏签到奖励失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_game_roleid(tajiduo_uid: str) -> tuple[str, str]:
    """
    API：apihub/api/getGameBindRole
    返回塔吉多社区账号绑定的游戏角色UID
    :return lev+roleName: 预定义好格式的游戏角色名和等级综合字符串
    :return roleId: 游戏角色UID
    """
    url = "https://bbs-api.tajiduo.com/apihub/api/getGameBindRole"
    data = {
        'gameId': "1289",  # 对应ID 1289=异环
        'uid': tajiduo_uid,  # 塔吉多社区账号UID
    }
    response = get_response(url, data, 2)
    if response["code"] == 0:
        roleName = response["data"]["roleName"]  # 游戏角色名
        roleId = response["data"]["roleId"]  # 游戏角色UID
        lev = response["data"]["lev"]  # 游戏角色等级
        serverId = response["data"]["serverId"]  # 服务器ID，目前应该没用，暂时保留
        return f"鉴定师「{roleName}」（Lv.{lev}）", roleId
    elif response["code"] == 401:
        # code 401 表示当前accessToken过期，需要使用refreshToken刷新两个Token，因为是刚刚获取的新令牌，出现此问题通常无法通过刷新令牌解决，直接抛出异常，让用户重新运行脚本
        raise SPException("accessToken失效", "accessToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 402:
        raise SPException("refreshToken失效", "refreshToken失效，请尝试重新运行脚本！")
    elif response["code"] == 500:
        raise SPException("获取游戏角色信息失败", f"获取游戏角色信息失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取游戏角色信息失败", f"获取游戏角色信息失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_signin_game(award: str, signin_time: int, roleName: str, roleId: str) -> str:
    """
    API：apihub/awapi/sign
    进行异环游戏签到的API
    :param award: 今天的游戏签到奖励
    :param signin_time: 当月签到天数（包含今天）
    :param roleId: 游戏角色UID
    :return message: 游戏签到执行相关的文本日志
    """
    message = ""
    url = "https://bbs-api.tajiduo.com/apihub/awapi/sign"
    data = {
        'gameId': "1289",  # 对应ID 1289=异环
        'roleId': roleId,  # 游戏角色UID
    }
    response = get_response(url, data, 1)
    if response["code"] == 0:
        message += f"异环游戏签到成功：{roleName}当月已签到 {signin_time} 天。今天的游戏签到奖励是{award}。"
        return message
    elif response["code"] == 401:
        # code 401 表示当前accessToken过期，需要使用refreshToken刷新两个Token，因为是刚刚获取的新令牌，出现此问题通常无法通过刷新令牌解决，直接抛出异常，让用户重新运行脚本
        raise SPException("accessToken失效", "accessToken失效，，请尝试重新运行脚本！")
    elif response["code"] == 402:
        raise SPException("refreshToken失效", "refreshToken失效，请尝试重新运行脚本！")
    elif response["code"] == 1511:
        message += f"游戏今天已经签到过了，今天的游戏签到奖励是 {award}。"
        return message
    else:
        raise SPException("游戏签到失败", f"游戏签到失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_response(url: str, data: dict[str, str], request_type: int) -> any:
    """
    返回处理为json的response
    :param url: 请求的url
    :param data: 请求的data或params
    :param request_type:用于区分请求类型，1为post，2为get
    :return 返回json化的response
    """
    headers1 = {
        **HEADERS_COMMON,
        'Content-Type': "application/x-www-form-urlencoded",
    }
    headers1 = {
        **HEADERS_COMMON_IOS,
        'Content-Type': "application/x-www-form-urlencoded",
        'ds': get_ds(),
    }
    headers2 = {
        'platform': 'android',
        'authorization': ACCESS_TOKEN,
        'uid': TAJIDUO_UID,
        'deviceid': UUID,
        'appversion': APPVERSION,
        'User-Agent': OKHTTP_UA,
    }
    headers2 = {
        **HEADERS_COMMON_IOS,
        'ds': get_ds(),
    }
    headers3 = {
        **HEADERS_COMMON_IOS,
        'ds': get_ds(),
    }
    last_exception = None
    for i in range(util.URL_RETRY_TIMES):
        try:
            if request_type == 1:
                response = requests.post(url, data=data, headers=headers1, timeout=util.URL_TIMEOUT)
            elif request_type == 2:
                response = requests.get(url, params=data, headers=headers2, timeout=util.URL_TIMEOUT)
            elif request_type == 3:
                response = requests.get(url, params=data, headers=headers3, timeout=util.URL_TIMEOUT)
            else:
                response = requests.post(url, data=data, headers=headers1, timeout=util.URL_TIMEOUT)  # 默认使用第一种headers
            response.raise_for_status()  # 如果响应状态码不是200，主动抛出异常进行重试访问
            return response.json()
        except requests.RequestException as e:
            last_exception = e
            util.send_log(f"URL访问失败（第{i + 1}次），HTTP Code {e.response.status_code}，{util.URL_RETRY_INTERVAL}秒后重试……", "warning")
            if i < util.URL_RETRY_TIMES:  # 失败时，等待指定秒后重试请求
                time.sleep(util.URL_RETRY_INTERVAL)
    raise last_exception  # 重试多次都失败时抛出最后一次失败时的异常，在主程序部分捕获，用于返回API访问失败导致程序运行失败的提示

if __name__ == "__main__":
    util.send_log("异环·塔吉多 每日签到 - 开始执行", "info")
    notify_content = ""  # 储存用于推送通知正文的消息内容
    value_check = ""  # 存储环境变量为空的变量名用于推送通知正文内容
    if ACCOUNT_TEL is None:
        value_check += "【tajiduo_tel】"
    if ACCOUNT_PASSWD is None:
        value_check += "【tajiduo_passwd】"
    if value_check == "":
        try:
            # 初始化部分，使用手机号+密码方式登录完美世界账号，并获取accessToken
            wanmei_token, wanmei_uid = do_wanmei_account_login()  # 登录完美世界账号获取账号uid和token
            util.send_log("已登录：完美世界游戏账号", "info")
            notify_content += "已登录：完美世界游戏账号\n\n"
            time.sleep(1)
            do_usercenter_login(wanmei_token, wanmei_uid)  # 登录塔吉多用户中心，将两个令牌和塔吉多社区uid写入全局变量
            util.send_log("已登录：塔吉多社区", "info")
            notify_content += "已登录：塔吉多社区\n\n"
            time.sleep(1)
            restart_flag = True  # 是否需要重新运行，默认为True用于启动第一次循环执行
            attempt = 0  # 最多重复执行3次
            util.send_log("登录令牌获取成功，开始执行签到任务……", "info")
            notify_content += "登录令牌获取成功，开始执行签到任务……\n\n"
            while restart_flag and attempt < 3:
                if attempt > 0:
                    util.send_log(f"社区交互任务执行出现意外的状况，开始重新执行，第{attempt + 2}次尝试中……", "warning")
                    notify_content += f"社区交互任务执行出现意外的状况，开始重新执行，第{attempt + 2}次尝试中……\n\n"
                restart_flag = False  # 循环开始将重新运行开关关闭
                attempt += 1  # 每次运行令运行次数计数+1，超出3次后不论是否成功都不再尝试
                # 获取用户今日任务完成情况，返回还需要进行多少次浏览帖子、点赞、社区签到、游戏签到、回复他人帖子次数的操作
                read, like, share, bbs_sign = get_tajiduo_taskprocess()
                time.sleep(2)
                # 获取今天游戏是否已经签到，以及当月签到天数（包含今天）
                game_sign, signin_time = get_signin_game()
                util.send_log(f"今日任务完成情况：点赞{' 已完成' if like == 0 else f'还需 {like} 次'}、浏览{' 已完成' if read == 0 else f'还需 {read} 次'}、分享{' 已完成' if share == 0 else f'还需 {share} 次'}、「塔吉多社区」签到 {'已完成' if bbs_sign == 0 else '未完成'}、「异环」签到 {'已完成' if game_sign == 0 else '未完成'}。", "info")
                notify_content += f"今日任务完成情况：点赞{' 已完成' if like == 0 else f'还需 {like} 次'}、浏览{' 已完成' if read == 0 else f'还需 {read} 次'}、分享{' 已完成' if share == 0 else f'还需 {share} 次'}、「塔吉多社区」签到 {'已完成' if bbs_sign == 0 else '未完成'}、「异环」签到 {'已完成' if game_sign == 0 else '未完成'}。\n\n"
                time.sleep(2)
                # 如果需要浏览/点赞/分享，则获取帖子列表，返回1组帖子的id和发帖人id
                if read > 0 or like > 0 or share > 0:
                    postIds= get_tajiduo_new_formlist()
                    util.send_log("已获取最新帖子列表，开始执行……", "info")
                    time.sleep(2)
                    # 如果需要点赞次数不为0，则执行点赞
                    if like > 0:
                        for i in range(like):
                            restart_flag = do_like(postIds[i])  # 执行点赞，每次传入一个帖子的id
                            if restart_flag:
                                util.send_log(f"执行第{i + 1}次点赞操作时出现意外错误，可能是操作的帖子被删除了，重新开始社区交互任务执行流程……", "warning")
                                break  # 访问API返回非致命的错误，跳出循环并重新执行获取新的帖子ID，此处用于中止当前for循环
                            else:
                                util.send_log(f"执行第{i + 1}次点赞操作完成……", "info")
                            time.sleep(1)
                        util.send_log(f"点赞任务完成，执行了{like}次点赞帖子操作；", "info")
                        notify_content += f"点赞任务完成，执行了{like}次点赞帖子操作；\n\n"
                    else:
                        util.send_log("点赞任务已完成，不需要进行操作；", "info")
                        notify_content += "点赞任务已完成，不需要进行操作；\n\n"
                    if restart_flag:
                        continue  # 访问API返回非致命的错误，跳出循环并重新执行获取新的帖子ID，此处用于中断后续代码运行并开始新的循环
                    # 如果需要浏览次数不为0，则执行浏览
                    if read > 0:
                        for i in range(read):
                            restart_flag = get_post_detail(postIds[i])  # 执行浏览，每次传入一个帖子的id
                            if restart_flag:
                                util.send_log(f"执行第{i + 1}次浏览帖子操作时出现意外错误，可能是操作的帖子被删除了，重新开始社区交互任务执行流程……", "warning")
                                break  # 访问API返回非致命的错误，跳出循环并重新执行获取新的帖子ID，此处用于中止当前for循环
                            else:
                                util.send_log(f"执行第{i + 1}次浏览帖子操作完成……", "info")
                            time.sleep(3)
                        util.send_log(f"浏览任务完成，执行了{read}次浏览帖子操作；", "info")
                        notify_content += f"浏览任务完成，执行了{read}次浏览帖子操作；\n\n"
                    else:
                        util.send_log("浏览任务已完成，不需要进行操作；", "info")
                        notify_content += "浏览任务已完成，不需要进行操作；\n\n"
                    if restart_flag:
                        continue  # 访问API返回非致命的错误，跳出循环并重新执行获取新的帖子ID，此处用于中断后续代码运行并开始新的循环
                    # 如果需要分享次数不为0，则执行分享帖子
                    if share > 0:
                        for i in range(share):
                            restart_flag = do_share(postIds[i])  # 执行分享，每次传入一个帖子的id
                            if restart_flag:
                                util.send_log(f"执行第{i + 1}次同步分享帖子任务进度操作时出现意外错误，重新开始社区交互任务执行流程……", "warning")
                                break  # 访问API返回非致命的错误，跳出循环并重新执行获取新的帖子ID，此处用于中止当前for循环
                            else:
                                util.send_log(f"执行第{i + 1}次同步分享帖子任务进度操作完成……", "info")
                            time.sleep(3)
                        util.send_log(f"分享任务完成，执行了{share}次分享帖子操作；", "info")
                        notify_content += f"分享任务完成，执行了{share}次分享帖子操作；\n\n"
                    else:
                        util.send_log("分享任务已完成，不需要进行操作；", "info")
                        notify_content += "分享任务已完成，不需要进行操作；\n\n"
                else:
                    util.send_log("今日社区交互任务均已完成，不需要进行操作；", "info")
                    notify_content += "今日社区交互任务均已完成，不需要进行操作；\n\n"
            if attempt == 2 and restart_flag:
                util.send_log("社区交互任务执行出现意外的状况，已重复尝试3次仍未成功，放弃此部分任务的执行！", "error")
                notify_content += "社区交互任务执行出现意外的状况，已重复尝试3次仍未成功，放弃此部分任务的执行！\n\n"

            # 如果需要社区签到，则执行签到
            if bbs_sign == 1:
                message_bbs_sign = do_signin_bbs()
                util.send_log(message_bbs_sign, "info")
                notify_content += f"{message_bbs_sign}\n\n"
                time.sleep(5)
            else:
                util.send_log(f"社区签到已完成，不需要进行操作；", "info")
                notify_content += f"社区签到已完成，不需要进行操作；\n\n"
            # 获取角色名称和id，用于游戏签到
            roleName, roleId = get_game_roleid(TAJIDUO_UID)
            # 获取今天游戏的签到奖励详情
            award = get_signin_game_awards_list(roleId)
            # 如果需要游戏签到，则执行签到
            if game_sign == 1:
                message_game_sign = do_signin_game(award, signin_time, roleName, roleId)
                util.send_log(message_game_sign, "info")
                notify_content += f"{message_game_sign}\n\n"
                time.sleep(5)
            else:
                util.send_log("异环游戏签到已完成，不需要进行操作；", "info")
                notify_content += f"异环游戏签到已完成，不需要进行操作。今天的游戏签到奖励是 {award}；\n\n"
            # 全部完成，最终推送
            util.send_log("异环·塔吉多 每日签到 - 执行完成", "info")
            util.send_notify("异环·签到：已完成", notify_content)
        except SPException as e:
            # 主动抛出的异常，用于在出现非访问失败的问题时中断后续函数执行
            util.send_log(e.content, "error")
            util.send_notify(f"【{e.title}】异环·签到", f"{notify_content}{e.content}")
        except requests.RequestException as e:
            # API访问失败的异常中断
            util.send_log(f"API请求失败 - {e}", "error")
            util.send_notify("【失败】异环·签到", f"{notify_content}API请求失败，请查看日志！\n\n错误信息：{e}")
        except Exception as e:
            # 其他所有异常
            util.send_log(f"程序运行报错 - {e}", "critical")
            util.send_log(f"{traceback.format_exc()}", "critical")
            util.send_notify("【程序报错】异环·签到", f"{notify_content}程序运行报错，请查看日志！\n\n错误信息：{e}")

    else:
        util.send_log(f"缺少环境变量配置！需要添加环境变量：{value_check}", "error")
        util.send_notify("【缺少环境变量】异环·签到",f"缺少环境变量，请添加以下环境变量后再使用：{value_check}")