"""
任务名称
name: 异环·塔吉多 每日签到
定时规则
cron: 0 3 0 * * ?
"""

import time
import requests
import traceback
from typing import List
from Utility.common import common_util as util
from Utility.common.common_util import SPException

# 获取一个随机生成的32位大写UUID4，在本次运行期间使用，用于给请求头的deviceid赋值
UUID = util.get_uuid(4, True, True)
# 从环境变量或本地ini文件获取Cookie，用于给请求头的Authorization赋值
ACCOUNT= util.get_config_env("tajiduo", section="COOKIE")[0] if util.USE_LOCAL_COOKIE else util.get_os_env("tajiduo")[0]

def get_tajiduo_taskprocess() -> tuple[int, ...]:
    """
    API：apihub/api/getUserTasks
    获取塔吉多社区用户的社区每日任务（task_list1）和一次性任务（task_list2）完成情况：
    :return 返回每日任务还差几次完成，like 每日点赞5次帖子、read 每日阅读3次帖子、share 每日分享1次帖子、bbs_sign 社区签到情况, bbs_sign_times 社区签到天数
    """
    bbs_sign = like = read = share = 0
    url = "https://bbs-api.tajiduo.com/apihub/api/getUserTasks?gid=1"
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
        return int(read), int(like), int(share), int(bbs_sign), int(bbs_sign_times)
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量tajiduo的值！")
    elif response["code"] == 500:
        raise SPException("获取社区每日任务进度失败", f"获取社区每日任务进度失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取社区每日任务进度失败",f"获取社区每日任务进度失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_tajiduo_new_formlist() -> List[int]:
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
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量tajiduo的值！")
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
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量tajiduo的值！")
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
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量tajiduo的值！")
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
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量tajiduo的值！")
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
        'platform': "wx_session",  # 对应ID 3=异环
        'postId': postId  # 帖子ID
    }
    response = get_response(url, data, 1)
    if response["code"] == 0:
        return False
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量tajiduo的值！")
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
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量tajiduo的值！")
    elif response["code"] == 1551:
        message += "塔吉多社区今天已经签到过了，无需签到。"
        return message
    elif response["code"] == 500:
        raise SPException("塔吉多签到失败", f"塔吉多签到失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("塔吉多签到失败", f"塔吉多签到失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

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
    url = ""
    data = {
        'gameId': "3",  # 对应ID 3=异环
        'serverId': server_id,
        'roleId': roleId,
    }
    response = get_response(url, data, 1)
    if response["code"] == 0:
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
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量tajiduo的值！")
    elif response["code"] == 500:
        raise SPException("获取异环游戏签到奖励失败", f"获取异环游戏签到奖励失败！请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("获取异环游戏签到奖励失败", f"获取异环游戏签到奖励失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_signin_game(award: str, signin_time: int, roleId: str, server_id: str) -> str:
    """
    API：encourage/signIn/v2
    进行异环游戏签到的API
    :param award: 今天的游戏签到奖励
    :param signin_time: 当月签到天数（包含今天）
    :param roleId: 游戏角色UID
    :param server_id: 游戏服务器ID
    :return message: 游戏签到执行相关的文本日志
    """
    message = ""
    url = ""
    data = {
        'gameId': "3",  # 对应ID 3=异环
        'serverId': server_id,
        'roleId': roleId,
        'reqMonth': util.get_format_datetime()["month"]  # 获取当前月份数字，不足2位则前面补0
    }
    response = get_response(url, data, 1)
    if response["code"] == 0:
        message += f"异环游戏签到成功：当月已签到 {signin_time} 天。今天的游戏签到奖励是{award}。"
        return message
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量tajiduo的值！")
    elif response["code"] == 1511:
        message += f"异环游戏今天已经签到过了，今天的游戏签到奖励是 {award}。"
        return message
    else:
        raise SPException("异环游戏签到失败", f"异环游戏签到失败！请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_response(url: str, data: dict[str, str], request_type: int) -> any:
    """
    返回处理为json的response
    :param url: 请求的url
    :param data: 请求的data或params
    :param request_type:用于区分请求类型，1为post，2为get
    :return 返回json化的response
    """
    headers1 = {
        'User-Agent': "HTAssistant/103 CFNetwork/3860.500.112 Darwin/25.4.0",
        'Accept-Encoding': "gzip, deflate",
        'platform': "ios",
        'uid': "0",
        'Accept': "application/json, text/plain, */*",
        'Accept-Language': "zh-CN,zh-Hans;q=0.9",
        'Host': "bbs-api.tajiduo.com",
        'Connection': "Keep-Alive",
        'Content-Type': "application/x-www-form-urlencoded",
        'appversion': "1.2.0",
        'deviceid': UUID,
        'Authorization': ACCOUNT
    }
    headers2 = {
        'User-Agent': "HTAssistant/103 CFNetwork/3860.500.112 Darwin/25.4.0",
        'Accept-Encoding': "gzip, deflate",
        'platform': "ios",
        'uid': "0",
        'Accept': "application/json, text/plain, */*",
        'Accept-Language': "zh-CN,zh-Hans;q=0.9",
        'Host': "bbs-api.tajiduo.com",
        'Connection': "Keep-Alive",
        'appversion': "1.2.0",
        'deviceid': UUID,
        'Authorization': ACCOUNT
    }
    last_exception = None
    for i in range(util.URL_RETRY_TIMES):
        try:
            if request_type == 1:
                response = requests.post(url, data=data, headers=headers1, timeout=util.URL_TIMEOUT)
            elif request_type == 2:
                response = requests.get(url, params=data, headers=headers2, timeout=util.URL_TIMEOUT)
            else:
                response = requests.post(url, data=data, headers=headers1, timeout=util.URL_TIMEOUT)  # 默认使用第一种headers
            response.raise_for_status()  # 如果响应状态码不是200，主动抛出异常进行重试访问
            return response.json()
        except requests.RequestException as e:
            last_exception = e
            util.send_log(f"URL访问失败（第{i + 1}次），{util.URL_RETRY_INTERVAL}秒后重试……", "warning")
            if i < util.URL_RETRY_TIMES:  # 失败时，等待指定秒后重试请求
                time.sleep(util.URL_RETRY_INTERVAL)
    raise last_exception  # 重试多次都失败时抛出最后一次失败时的异常，在主程序部分捕获，用于返回API访问失败导致程序运行失败的提示

if __name__ == "__main__":
    util.send_log("异环·塔吉多 每日签到 - 开始执行", "info")
    notify_content = ""  # 储存用于推送通知正文的消息内容
    value_check = ""  # 存储环境变量为空的变量名用于推送通知正文内容
    if ACCOUNT is None:
        value_check += "【tajiduo】"
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
                # 获取用户今日任务完成情况，返回还需要进行多少次浏览帖子、点赞、社区签到、游戏签到、回复他人帖子次数的操作
                read, like, share, bbs_sign = get_tajiduo_taskprocess()
                time.sleep(2)
                # 直接使用获取本月游戏签到奖励列表API，其中也会有今天是否签到的data
                game_sign, award = 0,"sss"
                #game_sign, award, signin_time = get_signin_game_awards_list(1,1)
                util.send_log(f"今日任务完成情况：点赞{' 已完成' if like == 0 else f'还需 {like} 次'}、浏览{' 已完成' if read == 0 else f'还需 {read} 次'}、分享{' 已完成' if share == 0 else f'还需 {share} 次'}、「塔吉多」签到 {'已完成' if bbs_sign == 0 else '未完成'}、「异环」签到 {'已完成' if game_sign == 0 else '未完成'}。", "info")
                notify_content += f"今日任务完成情况：点赞{' 已完成' if like == 0 else f'还需 {like} 次'}、浏览{' 已完成' if read == 0 else f'还需 {read} 次'}、分享{' 已完成' if share == 0 else f'还需 {share} 次'}、「塔吉多」签到 {'已完成' if bbs_sign == 0 else '未完成'}、「异环」签到 {'已完成' if game_sign == 0 else '未完成'}。\n\n"
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
            # 如果需要游戏签到，则执行签到
            if game_sign == 1:
                message_game_sign = do_signin_game()
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