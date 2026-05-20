"""
任务名称
name: 鸣潮·库街区 每日签到
定时规则
cron: 0 3 0 * * ?
"""

import time
import requests
import traceback
from Utility.common import common_util as util
from Utility.common.common_util import SPException

# 获取一个随机生成的UUID4，在本次运行期间使用，用于给请求头的devCode赋值
DEV_CODE = util.get_uuid(4, True, False)
# 获取一个随机生成的UUID4，在本次运行期间使用，用于给请求头的distinct_id赋值，值的后面需要加上指定后缀，且与devCode的UUID4不同
DISTINCT_ID = util.get_uuid(4, True, False) + "_3"
# 从环境变量或本地ini文件获取Cookie和UID
ACCOUNT, USER_ID = util.get_config_env("kurobbs", "kuro_uid", section="COOKIE") if util.USE_LOCAL_COOKIE else util.get_os_env("kurobbs", "kuro_uid")
# 请求头通用部分
HEADERS_COMMON = {
    'Accept-Encoding': "gzip, deflate",
    'Content-Type': "application/x-www-form-urlencoded",
    'source': "ios",
    'Host': "api.kurobbs.com",
    'Accept-Language': "zh-CN,zh-Hans;q=0.9",
    'Connection': "keep-alive",
    'token': ACCOUNT
}

def get_acw_tc() -> str:
    """
    模仿抓包获取的值的格式，随机生成一个68位的acw_tc值。
    前36位为标准UUID4（带横杠 - ），后32位为使用时间戳+前述生成的UUID组合进行SHA256后的值取前32位。
    :return 返回一个随机生成的68位acw_tc字符串
    """
    uuid = str(util.get_uuid(4,False,False))
    hash_part = util.get_sha256(f"{util.get_timestamp()}{uuid}")[:32]  # 截取32位哈希值补全tcw_tc的长度，也可以考虑使用MD5
    return f"{uuid}{hash_part}"

# 获取一个随机生成的acw_tc值，在本次运行期间使用，用于给请求头cookie赋值
# 尚不清楚这个值的产生方式，使用AI分析可能的组成方式而写出的生成代码，验证生成值可以使用，但无法确保一定可用
# 目前已经不需要这个值了，原实现方法做保留
#ACW_TC = get_acw_tc()

def old_get_kurobbs_userid() -> tuple[str, str]:
    """
    API：gamer/role/default
    ※注意：此API已不再使用，更换了新API，但目前此API仍然可以正常返回数据，仅作保留
    获取库街区社区账号默认绑定角色的UID、游戏所在服务器serverID，用于执行签到等操作：
    也有API user/mineV2，但只能查询库街区账号信息，无游戏角色信息
    :return 返回游戏角色roleId、游戏服务器serverID
    """
    url = "https://api.kurobbs.com/gamer/role/default"
    data = {
        'queryUserId': USER_ID  # 库街区账号UID
    }
    response = get_response(url, data, 2)
    if response["code"] == 200:
        response_data = response["data"]["defaultRoleList"]  # 获取包含账号所有游戏默认角色的信息数组
        for i in range(len(response_data)):
            if response_data[i]['gameId'] == 3:
                response_data = response_data[i]
                break  # 只获取鸣潮游戏的信息，找到后中断循环
        return  response_data["roleId"],response_data["serverId"]
    elif response["code"] == 220:
        raise SPException("Token失效", "Token失效，请更新环境变量kurobbs的值！")
    elif response["code"] == 500:
        raise SPException("获取账号ID失败", f"获取账号ID失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取账号ID失败",f"获取账号ID失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_kurobbs_userid() -> tuple[str, str]:
    """
    API：user/role/findUserDefaultRole
    新的API，返回数据格式与之前的API相同，仅URL变化和更新了新版本请求头
    获取库街区社区账号默认绑定角色的UID、游戏所在服务器serverID，用于执行签到等操作：
    也有API user/mineV2，但只能查询库街区账号信息，无游戏角色信息
    :return 返回游戏角色roleId、游戏服务器serverID
    """
    url = "https://api.kurobbs.com/user/role/findUserDefaultRole"
    data = {
        'queryUserId': USER_ID  # 库街区账号UID
    }
    response = get_response(url, data, 2)
    if response["code"] == 200:
        response_data = response["data"]["defaultRoleList"]  # 获取包含账号所有游戏默认角色的信息数组
        for i in range(len(response_data)):
            if response_data[i]['gameId'] == 3:
                response_data = response_data[i]
                break  # 只获取鸣潮游戏的信息，找到后中断循环
        return  response_data["roleId"],response_data["serverId"]
    elif response["code"] == 220:
        raise SPException("Token失效", "Token失效，请更新环境变量kurobbs的值！")
    elif response["code"] == 500:
        raise SPException("获取账号ID失败", f"获取账号ID失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取账号ID失败",f"获取账号ID失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_kurobbs_taskprocess() -> tuple[int, ...]:
    """
    API：encourage/level/getTaskProcess
    获取库街区社区用户的社区每日任务和一次性任务完成情况：
    :return 返回每日任务还差几次完成，like 每日点赞5次帖子、read 每日阅读3次帖子、share 每日分享1次帖子、bbs_sign 社区签到情况
    """
    bbs_sign = like = read = share = 0
    url = "https://api.kurobbs.com/encourage/level/getTaskProcess"
    data = {
        'gameId': "0",  # 对应ID 0 库街区
        #'userId': USER_ID  # 库街区账号UID，目前此API已经不需要此值了
    }
    response = get_response(url, data, 2)
    if response["code"] == 200:
        data = response["data"]["dailyTask"]
        for i in range(len(data)):
            if data[i]['remark'] == "点赞5次":
                like = data[i]['needActionTimes'] - data[i]['completeTimes']
            if data[i]['remark'] == "浏览3篇帖子":
                read = data[i]['needActionTimes'] - data[i]['completeTimes']
            if data[i]['remark'] == "分享1次帖子":
                share = data[i]['needActionTimes'] - data[i]['completeTimes']
            if data[i]['remark'] == "用户签到":
                bbs_sign = data[i]['needActionTimes'] - data[i]['completeTimes']
        return int(read), int(like), int(share), int(bbs_sign)
    elif response["code"] == 220:
        raise SPException("Token失效", "Token失效，请更新环境变量kurobbs的值！")
    elif response["code"] == 500:
        raise SPException("获取社区每日任务进度失败", f"获取社区每日任务进度失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取社区每日任务进度失败",f"获取社区每日任务进度失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_kurobbs_new_formlist() -> tuple[str, str]:
    """
    API：forum/list
    获取库街区鸣潮-今州茶馆分版下最新发布的帖子列表
    用于获取帖子ID进行点赞和浏览的每日任务
    获取最新发布的用户水区是确保每天获取的第一页帖子列表一定是新帖子，防止对已经浏览/点赞过的帖子再次处理导致任务进度不增加
    但目前其任务进度使用重复浏览、点赞取消后再点赞的方式，也会计入完成次数
    :return 返回帖子ID postId 和作者ID userId
    """
    url = "https://api.kurobbs.com/forum/list"
    data = {
        'forumId': "10",  # 对应版块ID 2 战双帕弥什·推荐 | 9 鸣潮·推荐 | 10 鸣潮·今州茶馆
        'gameId': "3",  # 对应ID 0 库街区 | 2 战双帕弥什 | 3=鸣潮
        'pageIndex': "1",  # 页码
        'pageSize': "20",  # 一页内容数量
        'searchType': "1",  # 排序规则，1 最新发布 | 2 最新回复 | 3 默认排序
        'timeType': "0",  # 未知用途
        'topicId': "",  # 话题ID
    }
    response = get_response(url, data, 2)
    if response["code"] == 200:
        data = response["data"]["postList"][0]
        return data["postId"], data["userId"]
    elif response["code"] == 220:
        raise SPException("Token失效", "Token失效，请更新环境变量kurobbs的值！")
    elif response["code"] == 500:
        raise SPException("获取最新帖子列表失败", f"获取最新帖子列表失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取最新帖子列表失败", f"获取最新帖子列表失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_post_detail(postId: str) -> bool:
    """
    API：forum/getPostDetail
    浏览帖子详情的API，用于完成每日浏览任务
    :param postId: 帖子ID
    :return 返回布尔值，True为帖子被删除需要重新执行一遍，False为正常处理
    """
    url = "https://api.kurobbs.com/forum/getPostDetail"
    data = {
        'isOnlyPublisher': "0",  # 是否为付费专享帖子
        'postId': postId,  # 帖子ID
        'showOrderType': "2"  # 未知用途
    }
    response = get_response(url, data, 2)
    if response["code"] == 200:
        return False
    elif response["code"] == 220:
        raise SPException("Token失效", "Token失效，请更新环境变量kurobbs的值！")
    elif response["code"] == 501:
        return True  # 这篇帖子被删除，返回False令程序从获取新的帖子ID步骤从新开始执行
    elif response["code"] == 500:
        raise SPException("浏览帖子任务失败", f"浏览帖子任务失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("浏览帖子任务失败", f"浏览帖子任务失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_like(postId: str,toUserId: str) -> bool:
    """
    API：forum/like
    进行点赞的API，用于完成每日点赞任务
    为了防止传入的帖子本身是已经点过赞的，导致第一次点赞无效
    因此第一次点赞前会先调用取消点赞API确保帖子是没有点赞的状态
    :param postId: 帖子ID
    :param toUserId: 帖子作者ID
    :return 返回布尔值，True为帖子被删除需要重新执行一遍，False为正常处理
    """
    url = "https://api.kurobbs.com/forum/like"
    data = {
        'forumId': "10",  # 对应版块ID 10=今州茶馆
        'gameId': "3",  # 对应ID 3=鸣潮
        'likeType': "1",  # 未知用途
        'operateType': "1",  # 1为点赞，2为取消点赞
        'postCommentId': "0",  # 未知用途
        'postCommentReplyId': "0",  # 未知用途
        'postId': postId,  # 帖子ID
        'postType': "1",  # 未知用途
        'toUserId': toUserId  # 帖子作者ID
    }
    response = get_response(url, data, 2)
    if response["code"] == 200:
        return False
    elif response["code"] == 220:
        raise SPException("Token失效", "Token失效，请更新环境变量kurobbs的值！")
    elif response["code"] == 501:
        return True  # 这篇帖子被删除，返回False令程序从获取新的帖子ID步骤从新开始执行
    elif response["code"] == 500:
        raise SPException("社区点赞任务失败", f"社区点赞任务失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("社区点赞任务失败", f"社区点赞任务失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_unlike(postId: str,toUserId: str) -> bool:
    """
    API：forum/like
    进行取消点赞的API
    与点赞API相同，唯一区别是传入的operateType参数值从1改为2
    :param postId: 帖子ID
    :param toUserId: 帖子作者ID
    :return 返回布尔值，True为帖子被删除需要重新执行一遍，False为正常处理
    """
    url = "https://api.kurobbs.com/forum/like"
    data = {
        'forumId': "10",  # 对应版块ID 10=今州茶馆
        'gameId': "3",  # 对应ID 3=鸣潮
        'likeType': "1",  # 未知用途
        'operateType': "2",  # 1为点赞，2为取消点赞
        'postCommentId': "0",  # 未知用途
        'postCommentReplyId': "0",  # 未知用途
        'postId': postId,  # 帖子ID
        'postType': "1",  # 未知用途
        'toUserId': toUserId  # 帖子作者ID
    }
    response = get_response(url, data, 2)
    if response["code"] == 200:
        return False
    elif response["code"] == 220:
        raise SPException("Token失效", "Token失效，请更新环境变量kurobbs的值！")
    elif response["code"] == 501:
        return True  # 这篇帖子被删除，返回False令程序从获取新的帖子ID步骤从新开始执行
    elif response["code"] == 500:
        raise SPException("社区点赞任务失败", f"社区点赞任务失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("社区点赞任务失败", f"社区点赞任务失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_share(postId: str) -> bool:
    """
    API：encourage/level/shareTask
    进行分享任务进度提交的API
    :param postId: 帖子ID
    :return 返回布尔值，True为帖子被删除需要重新执行一遍，False为正常处理
    """
    url = "https://api.kurobbs.com/encourage/level/shareTask"
    data = {
        'gameId': "3",  # 对应ID 3=鸣潮
        'postId': postId  # 帖子ID
    }
    response = get_response(url, data, 2)
    if response["code"] == 200:
        return False
    elif response["code"] == 220:
        raise SPException("Token失效", "Token失效，请更新环境变量kurobbs的值！")
    elif response["code"] == 501:
        return True  # 这篇帖子被删除，返回False令程序从获取新的帖子ID步骤从新开始执行
    elif response["code"] == 500:
        raise SPException("社区分享任务失败", f"社区分享任务失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("社区分享任务失败", f"社区分享任务失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_signin_bbs() -> str:
    """
    API：user/signIn
    进行库街区签到的API
    :return message: 社区签到执行相关的文本日志
    """
    message = ""
    url = "https://api.kurobbs.com/user/signIn"
    data = {
        'gameId': "2",  # 对应ID 2=战双帕弥什，社区签到无论在哪个游戏板块签到都使用此分区的ID签到
        'geeTestData': ""
    }
    response = get_response(url, data, 2)
    if response["code"] == 200:
        response_data = response["data"]
        response_award = response_data["gainVoList"]
        message += f"库街区社区签到成功：当前连续签到 {response_data['continueDays']} 天，累计签到 {response_data['totalSignInDay']} 天。今天的签到奖励是"
        for i in range(len(response_award)):
            if response_award[i]["gainTyp"] == 2:
                message += f"「库洛币」*{response_award[i]['gainValue']}"
            else:
                message += f"「未知奖励」*{response_award[i]['gainValue']}"
            if i + 1 < len(response_award):
                message += "、"
            else:
                message += "。"
        return message
    elif response["code"] == 220:
        raise SPException("Token失效", "Token失效，请更新环境变量kurobbs的值！")
    elif response["code"] == 1551:
        message += "库街区社区今天已经签到过了，无需签到。"
        return message
    elif response["code"] == 500:
        raise SPException("库街区签到失败", f"库街区签到失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("库街区签到失败", f"库街区签到失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_signin_game_awards_list(roleId: str, server_id: str) -> tuple[int, str, str]:
    """
    API：encourage/signIn/initSignInV2
    返回当前月份游戏签到的奖励详情列表，与当前月份用户已经签到天数、可使用补签次数等信息
    :param roleId: 游戏角色UID
    :param server_id: 游戏服务器ID
    :return game_sign: 今天是否已经签到，0为签到过，1为未签到
    :return award: 今天的游戏签到奖励
    :return signin_time: 当月签到天数（包含今天）
    """
    url = "https://api.kurobbs.com/encourage/signIn/initSignInV2"
    data = {
        'gameId': "3",  # 对应ID 3=鸣潮
        'serverId': server_id,
        'roleId': roleId,
        'userId': USER_ID
    }
    response = get_response(url, data, 1)
    if response["code"] == 200:
        award = "「未知奖励」"
        # 确定今天游戏是否签到，response["data"]["isSigIn"]的值true为签到过，false为没有签到
        if response["data"]["isSigIn"]:
            game_sign = 0
            signin_time = response["data"]["sigInNum"]  # 获取当月签到天数，今天已经签过到了，因此直接以此签到天数获取今天签到奖励内容
        else:
            game_sign = 1
            signin_time = response["data"]["sigInNum"] + 1  # 获取当月签到天数，今天未签到，因此需要+1天，获取今天签到后的天数，以此来获取对应的dayAwardId和签到奖励内容
        award_list = response["data"]["signInGoodsConfigs"]  # 当月奖励详情列表
        for i in range(len(award_list)):
            if award_list[i]["serialNum"] == signin_time - 1:  # 由于serialNum是从0开始算，签到天数从1开始算，因此需要-1
                award = f"「{award_list[i]['goodsName']}」*{award_list[i]['goodsNum']}"
                break  # 找到当天的奖励了，直接中断for循环
        if "loopSignName" in response["data"]:
            event_award_name = response["data"]["loopSignName"]
            event_signin_time = response["data"]["loopSignNum"]
            event_award_list = response["data"]["signLoopGoodsList"]
            if not response["data"]["isSigIn"]:
                event_signin_time = event_signin_time + 1  # 今天未签到，因此需要+1天，
            for i in range(len(event_award_list)):
                if event_award_list[i]["serialNum"] == event_signin_time - 1:  # 由于serialNum是从0开始算，签到天数从1开始算，因此需要-1
                    award = award + f"、限时活动「{event_award_name}」的奖励是「{event_award_list[i]['goodsName']}」*{event_award_list[i]['goodsNum']}"
                    break  # 找到当天的奖励了，直接中断for循环
        return game_sign, award, signin_time
    elif response["code"] == 220:
        raise SPException("Token失效", "Token失效，请更新环境变量kurobbs的值！")
    elif response["code"] == 500:
        raise SPException("获取鸣潮游戏签到奖励失败", f"获取鸣潮游戏签到奖励失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取鸣潮游戏签到奖励失败", f"获取鸣潮游戏签到奖励失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_signin_game(award: str, signin_time: int, roleId: str, server_id: str) -> str:
    """
    API：encourage/signIn/v2
    进行鸣潮游戏签到的API
    :param award: 今天的游戏签到奖励
    :param signin_time: 当月签到天数（包含今天）
    :param roleId: 游戏角色UID
    :param server_id: 游戏服务器ID
    :return message: 游戏签到执行相关的文本日志
    """
    message = ""
    url = "https://api.kurobbs.com/encourage/signIn/v2"
    data = {
        'gameId': "3",  # 对应ID 3=鸣潮
        'serverId': server_id,
        'roleId': roleId,
        'userId': USER_ID,
        'reqMonth': util.get_format_datetime()["month"]  # 获取当前月份数字，不足2位则前面补0
    }
    response = get_response(url, data, 1)
    if response["code"] == 200:
        message += f"鸣潮游戏签到成功：当月已签到 {signin_time} 天。今天的游戏签到奖励是{award}。"
        return message
    elif response["code"] == 220:
        raise SPException("Token失效", "Token失效，请更新环境变量kurobbs的值！")
    elif response["code"] == 1511:
        message += f"鸣潮游戏今天已经签到过了，今天的游戏签到奖励是 {award}。"
        return message
    else:
        raise SPException("鸣潮游戏签到失败", f"鸣潮游戏签到失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_response(url: str, data: dict[str, str], headers_type: int) -> any:
    """
    返回处理为json的response
    :param url: 请求的url
    :param data: 请求的data
    :param headers_type:存在两种headers，第一种用于部分执行操作的API（如游戏签到），第二种用于大部分社区功能相关的API
    :return 返回json化的response
    """
    headers1 = {
        **HEADERS_COMMON,
        'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko)  KuroGameBox/3.0.3",
        'Accept': "application/json, text/plain, */*",
        'Origin': "https://web-static.kurobbs.com",
        'Sec-Fetch-Site': "same-site",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Priority': "u=3, i",
        'devCode': "111.16.160.144, Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko)  KuroGameBox/3.0.3",
    }
    headers2 = {
        **HEADERS_COMMON,
        'User-Agent': "KuroGameBox/20260513195311 CFNetwork/3860.600.12 Darwin/25.5.0",
        'channelId': "1",
        'version': "3.0.3",
        'distinct_id': DISTINCT_ID,
        'channel': "appstore",
        'Accept': "*/*",
        'devCode': DEV_CODE,
        'ip': "192.168.1.2",
        'lang': "zh-Hans",
        'model': "iPhone15,4",
        'osVersion': "26.5",
    }
    last_exception = None
    for i in range(util.URL_RETRY_TIMES):
        try:
            if headers_type == 1:
                response = requests.post(url, data=data, headers=headers1, timeout=util.URL_TIMEOUT)
            elif headers_type == 2:
                response = requests.post(url, data=data, headers=headers2, timeout=util.URL_TIMEOUT)
            else:
                response = requests.post(url, data=data, headers=headers2, timeout=util.URL_TIMEOUT)  # 默认使用第二种headers
            response.raise_for_status()  # 如果响应状态码不是200，主动抛出异常进行重试访问
            return response.json()
        except requests.RequestException as e:
            last_exception = e
            util.send_log(f"URL访问失败（第{i + 1}次），{util.URL_RETRY_INTERVAL}秒后重试……", "warning")
            if i < util.URL_RETRY_TIMES:  # 失败时，等待指定秒后重试请求
                time.sleep(util.URL_RETRY_INTERVAL)
    raise last_exception  # 重试多次都失败时抛出最后一次失败时的异常，在主程序部分捕获，用于返回API访问失败导致程序运行失败的提示

if __name__ == "__main__":
    util.send_log("鸣潮·库街区 每日签到 - 开始执行", "info")
    notify_content = ""  # 储存用于推送通知正文的消息内容
    value_check = ""  # 存储环境变量为空的变量名用于推送通知正文内容
    if ACCOUNT is None:
        value_check += "【kurobbs】"
    if USER_ID is None:
        value_check += "【kuro_uid】"
    if value_check == "":
        try:
            restart_flag = True  # 是否需要重新运行，默认为True用于启动第一次循环执行
            attempt = 0  # 最多重复执行3次
            while restart_flag and attempt < 3:
                if attempt > 0:
                    util.send_log(f"社区交互任务执行出现意外的状况，开始重新执行，第{attempt + 2}次尝试中……", "warning")
                    notify_content += f"社区交互任务执行出现意外的状况，开始重新执行，第{attempt + 2}次尝试中……\n\n"
                restart_flag = False  # 循环开始将重新运行开关关闭
                attempt += 1  # 每次运行令运行次数计数+1，超出3次后不论是否成功都不再尝试
                # 获取用户库街区账号绑定的默认角色UID和服务器ID
                roleId, server_id = get_kurobbs_userid()
                util.send_log(f"已获取用户库街区账号绑定的默认角色UID：{roleId}，账号所在服务器ID：{server_id}。", "info")
                notify_content += f"已获取用户库街区账号绑定的默认角色UID：{roleId}。\n\n"
                time.sleep(2)
                # 获取用户今日任务完成情况，返回还需要进行多少次浏览帖子、点赞、社区签到、游戏签到、回复他人帖子次数的操作
                read, like, share, bbs_sign = get_kurobbs_taskprocess()
                time.sleep(2)
                # 直接使用获取本月游戏签到奖励列表API，其中也会有今天是否签到的data
                game_sign, award, signin_time = get_signin_game_awards_list(roleId, server_id)
                util.send_log(f"今日任务完成情况：点赞{' 已完成' if like == 0 else f'还需 {like} 次'}、浏览{' 已完成' if read == 0 else f'还需 {read} 次'}、分享{' 已完成' if share == 0 else f'还需 {share} 次'}、「库街区」签到 {'已完成' if bbs_sign == 0 else '未完成'}、「鸣潮」签到 {'已完成' if game_sign == 0 else '未完成'}。", "info")
                notify_content += f"今日任务完成情况：点赞{' 已完成' if like == 0 else f'还需 {like} 次'}、浏览{' 已完成' if read == 0 else f'还需 {read} 次'}、分享{' 已完成' if share == 0 else f'还需 {share} 次'}、「库街区」签到 {'已完成' if bbs_sign == 0 else '未完成'}、「鸣潮」签到 {'已完成' if game_sign == 0 else '未完成'}。\n\n"
                time.sleep(2)
                # 如果需要浏览/点赞/分享，则获取帖子列表，返回1组帖子的id和发帖人id
                if read > 0 or like > 0 or share > 0:
                    postId, postUserId = get_kurobbs_new_formlist()
                    util.send_log("已获取最新帖子列表，开始执行……", "info")
                    time.sleep(2)
                    # 如果需要点赞次数不为0，则执行点赞
                    if like > 0:
                        for i in range(like):
                            restart_flag = do_unlike(postId, postUserId)  # 先取消点赞，防止这个帖子本身就被用户点过赞了导致第一次点赞不计入任务完成数中
                            if restart_flag:
                                util.send_log(f"执行第{i+1}次取消点赞操作时出现意外错误，可能是操作的帖子被删除了，重新开始社区交互任务执行流程……", "warning")
                                break  # 访问API返回非致命的错误，跳出循环并重新执行获取新的帖子ID，此处用于中止当前for循环
                            else:
                                util.send_log(f"执行第{i + 1}次取消点赞操作完成……", "info")
                            time.sleep(1)
                            restart_flag = do_like(postId, postUserId)  # 执行点赞
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
                            restart_flag = get_post_detail(postId)
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
                            restart_flag = do_share(postId)
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
                util.send_log("社区签到已完成，不需要进行操作；", "info")
                notify_content += "社区签到已完成，不需要进行操作；\n\n"
            # 如果需要游戏签到，则执行签到
            if game_sign == 1:
                message_game_sign = do_signin_game(award, signin_time, roleId, server_id)
                util.send_log(message_game_sign, "info")
                notify_content += f"{message_game_sign}\n\n"
                time.sleep(5)
            else:
                util.send_log("鸣潮游戏签到已完成，不需要进行操作；", "info")
                notify_content += f"鸣潮游戏签到已完成，不需要进行操作。今天的游戏签到奖励是 {award}；\n\n"
            # 全部完成，最终推送
            util.send_log("鸣潮·库街区 每日签到 - 执行完成", "info")
            util.send_notify("鸣潮·签到：已完成", notify_content)
        except SPException as e:
            # 主动抛出的异常，用于在出现非访问失败的问题时中断后续函数执行
            util.send_log(e.content, "error")
            util.send_notify(f"【{e.title}】鸣潮·签到", f"{notify_content}{e.content}")
        except requests.RequestException as e:
            # API访问失败的异常中断
            util.send_log(f"API请求失败 - {e}", "error")
            util.send_notify("【失败】鸣潮·签到", f"{notify_content}API请求失败，请查看日志！\n\n错误信息：{e}")
        except Exception as e:
            # 其他所有异常
            util.send_log(f"程序运行报错 - {e}", "critical")
            util.send_log(f"{traceback.format_exc()}", "critical")
            util.send_notify("【程序报错】鸣潮·签到", f"{notify_content}程序运行报错，请查看日志！\n\n错误信息：{e}")

    else:
        util.send_log(f"缺少环境变量配置！需要添加环境变量：{value_check}", "error")
        util.send_notify("【缺少环境变量】鸣潮·签到",f"缺少环境变量，请添加以下环境变量后再使用：{value_check}")