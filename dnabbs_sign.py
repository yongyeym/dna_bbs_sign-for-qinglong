"""
任务名称
name: 二重螺旋·皎皎角 每日签到
定时规则
cron: 0 3 0 * * ?
"""

import time
import traceback
import requests
from Utility.common import common_util as util
from Utility.common.common_util import SPException

# 用于给不同API的请求头Content-Length赋值
CONTENT_LENGTH_NUM = {"forum/list" : "78", "forum/like" : "146", "shareTask" : "10", "getPostDetail" : "58", "TaskProcess" : "10", "signIn" : "10", "signInGame" : "38", "signin/show" : "10", "user/mineV2" : "6"}
# 获取一个随机生成的UUID，在本次运行期间使用，用于给请求头的devCode赋值
UUID = util.get_uuid(4, True, False)
# 从环境变量获取Cookie
ACCOUNT = util.get_os_env("dnabbs")[0]

def get_dnabbs_userid():
    """
    API：user/mineV2
    获取皎皎角社区账号的UID，用于获取社区每日任务完成情况：
    """
    url = "https://dnabbs-api.yingxiong.com/user/mineV2"
    data = {
        'type': "1"  # 未知用途
    }
    response = get_response(url, data, CONTENT_LENGTH_NUM["user/mineV2"])
    if response["code"] == 200:
        return  response["data"]["mine"]["userId"]
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量dnabbs的值！")
    elif response["code"] == 500:
        raise SPException("失败", f"请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("失败",f"请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_dnabbs_taskprocess(userId):
    """
    API：encourage/level/getTaskProcess
    获取皎皎角社区用户的社区每日任何和一次性任务完成情况：
    bbs_sign 社区签到情况
    game_sign 游戏签到情况
    like 每日点赞5次帖子
    read 每日阅读3次帖子
    share 每日分享1次帖子
    comment 每日回复他人帖子5次

    返回JSON：
    completeTimes：当前完成的次数
    times：需要完成的次数
    gainExp：皎皎角社区用户经验
    gainGold：皎皎角社区金币
    process：当前进度，0-1的小数形式表示百分比进度
    remark：任务名称
    skipType：对于每日任务，这个值恒为0
    """
    bbs_sign = like = read = share = comment = 0
    url = "https://dnabbs-api.yingxiong.com/encourage/level/getTaskProcess"
    data = {
        'gameId': "268",  # 对应游戏ID 268=二重螺旋
        'userId': userId  # 用户ID
    }
    response = get_response(url, data, CONTENT_LENGTH_NUM["TaskProcess"])
    if response["code"] == 200:
        data = response["data"]["dailyTask"]
        for i in range(len(data)):
            if data[i]['remark'] == "完成5次点赞":
                like = data[i]['times'] - data[i]['completeTimes']
            if data[i]['remark'] == "浏览3篇帖子":
                read = data[i]['times'] - data[i]['completeTimes']
            if data[i]['remark'] == "分享1篇内容":
                share = data[i]['times'] - data[i]['completeTimes']
            if data[i]['remark'] == "回复他人帖子5次":
                comment = data[i]['times'] - data[i]['completeTimes']
            if data[i]['remark'] == "签到":
                bbs_sign = data[i]['times'] - data[i]['completeTimes']
        return int(read), int(like), int(share), int(bbs_sign), int(comment)
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量dnabbs的值！")
    elif response["code"] == 500:
        raise SPException("失败", f"请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("失败",f"请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_dnabbs_new_formlist():
    """
    API：forum/list
    获取皎皎角社区用户水区分版下最新发布的帖子列表
    用于获取帖子ID进行点赞和浏览的每日任务
    获取最新发布的用户水区是确保每天获取的第一页帖子列表一定是新帖子，防止对已经浏览/点赞过的帖子再次处理导致任务进度不增加
    但目前其任务进度使用重复浏览、点赞取消后再点赞的方式，也会计入完成次数
    """
    url = "https://dnabbs-api.yingxiong.com/forum/list"
    data = {
        'forumId': "47",  # 皎皎角社区板块ID，46 全部 | 47 水仙平原 | 48 官方 | 49 活动 | 50 攻略
        'gameId': "268",  # 对应游戏ID 268=二重螺旋
        'pageIndex': "1",  # 页码
        'pageSize': "20",  # 一页内容数量
        'searchType': "1",  # 排序规则，1 最新发布 | 2 最新回复 | 4 精华
        'timeType': "0",  # 未知用途
        'topicId': "",  # 话题ID
    }
    response = get_response(url, data, CONTENT_LENGTH_NUM["forum/list"])
    if response["code"] == 200:
        data = response["data"]["postList"][0]
        return data["postId"], data["userId"]
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量dnabbs的值！")
    elif response["code"] == 500:
        raise SPException("失败", f"请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("失败", f"请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_post_detail(postId):
    """
    API：forum/getPostDetail
    浏览帖子详情的API，用于完成每日浏览任务
    """
    url = "https://dnabbs-api.yingxiong.com/forum/getPostDetail"
    data = {
        'isOnlyPublisher': "1",  # 是否为付费专享帖子
        'postId': postId,  # 帖子ID
        'showOrderType': "1"  # 未知用途
    }
    response = get_response(url, data, CONTENT_LENGTH_NUM["getPostDetail"])
    if response["code"] == 200:
        return False
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量dnabbs的值！")
    elif response["code"] == 501:
        return True  # 这篇帖子被删除，返回False令程序从获取新的帖子ID步骤从新开始执行
    elif response["code"] == 500:
        raise SPException("失败", f"请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("失败", f"请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_like(postId,toUserId):
    """
    API：forum/like
    进行点赞的API，用于完成每日点赞任务
    为了防止传入的帖子本身是已经点过赞的，导致第一次点赞无效
    因此第一次点赞前会先调用取消点赞API确保帖子是没有点赞的状态
    """
    url = "https://dnabbs-api.yingxiong.com/forum/like"
    data = {
        'forumId': "47",  # 皎皎角社区板块ID
        'gameId': "268",  # 对应游戏ID 268=二重螺旋
        'likeType': "1",  # 未知用途
        'operateType': "1",  # 1为点赞，2为取消点赞
        'postCommentId': "",  # 未知用途
        'postCommentReplyId': "",  # 未知用途
        'postId': postId,  # 帖子ID
        'postType': "3",  # 未知用途
        'toUserId': toUserId  # 帖子作者ID
    }
    response = get_response(url, data, CONTENT_LENGTH_NUM["forum/like"])
    if response["code"] == 200:
        return False
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量dnabbs的值！")
    elif response["code"] == 501:
        return True  # 这篇帖子被删除，返回False令程序从获取新的帖子ID步骤从新开始执行
    elif response["code"] == 500:
        raise SPException("失败", f"请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("失败", f"请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_unlike(postId,toUserId):
    """
    API：forum/like
    进行取消点赞的API
    与点赞API相同，唯一区别是传入的operateType参数值从1改为2
    """
    url = "https://dnabbs-api.yingxiong.com/forum/like"
    data = {
        'forumId': "47",  # 皎皎角社区板块ID
        'gameId': "268",  # 对应游戏ID 268=二重螺旋
        'likeType': "1",  # 未知用途
        'operateType': "2",  # 1为点赞，2为取消点赞
        'postCommentId': "",  # 未知用途
        'postCommentReplyId': "",  # 未知用途
        'postId': postId,  # 帖子ID
        'postType': "3",  # 未知用途
        'toUserId': toUserId  # 帖子作者ID
    }
    response = get_response(url, data, CONTENT_LENGTH_NUM["forum/like"])
    if response["code"] == 200:
        return False
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量dnabbs的值！")
    elif response["code"] == 501:
        return True  # 这篇帖子被删除，返回False令程序从获取新的帖子ID步骤从新开始执行
    elif response["code"] == 500:
        raise SPException("失败", f"请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("失败", f"请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_share():
    """
    API：encourage/level/shareTask
    进行分享任务进度提交的API
    """
    url = "https://dnabbs-api.yingxiong.com/encourage/level/shareTask"
    data = {
        'gameId': "268"  # 对应游戏ID 268=二重螺旋
    }
    response = get_response(url, data, CONTENT_LENGTH_NUM["shareTask"])
    if response["code"] == 200:
        return False
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量dnabbs的值！")
    elif response["code"] == 501:
        return True  # 这篇帖子被删除，返回False令程序从获取新的帖子ID步骤从新开始执行
    elif response["code"] == 500:
        raise SPException("失败", f"请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("失败", f"请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_signin_bbs():
    """
    API：user/signIn
    进行皎皎角社区签到的API

    返回JSON：
    continuitySignInDay：当前连续签到天数
    totalSignInDay：累计签到天数
    hasNewDraw：未知用途
    hasNewProduct：未知用途
    data-gainVoList：本次签到的奖励内容和数量，gainTyp 1为皎皎积分，2为社区经验
    """
    message = ""
    url = "https://dnabbs-api.yingxiong.com/user/signIn"
    data = {
        'gameId': "268"  # 对应游戏ID 268=二重螺旋
    }
    response = get_response(url, data, CONTENT_LENGTH_NUM["signIn"])
    if response["code"] == 200:
        response_data = response["data"]
        response_award = response_data["gainVoList"]
        message += f"皎皎角社区签到成功：当前连续签到 {response_data['continuitySignInDay']} 天，累计签到 {response_data['totalSignInDay']} 天。今天的签到奖励是"
        for i in range(len(response_award)):
            if response_award[i]["gainTyp"] == 1:
                message += f"「皎皎积分」*{response_award[i]['gainValue']}"
            elif response_award[i]["gainTyp"] == 2:
                message += f"「社区经验」*{response_award[i]['gainValue']}"
            else:
                message += f"「未知奖励」*{response_award[i]['gainValue']}"
            if i + 1 < len(response_award):
                message += "、"
            else:
                message += "。"
        return message
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量dnabbs的值！")
    elif response["code"] == 10000:
        #  重复签到情况
        message += "皎皎角社区今天已经签到过了，无需签到。"
        return message
    elif response["code"] == 500:
        raise SPException("失败", f"请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("失败", f"请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_signin_game_awards_list():
    """
    API：encourage/signin/show
    返回当前月份游戏签到的奖励详情列表，与当前月份用户已经签到天数、可使用补签次数等信息
    """
    url = "https://dnabbs-api.yingxiong.com/encourage/signin/show"
    data = {
        'gameId': "268"  # 对应游戏ID 268=二重螺旋
    }
    response = get_response(url, data, CONTENT_LENGTH_NUM["signin/show"])
    if response["code"] == 200:
        # 确定今天游戏是否签到，true为签到过，false为没有签到
        if response["data"]["todaySignin"]:
            game_sign = 0
            signin_time = response["data"]["signinTime"]  # 获取当月签到天数，今天已经签过到了，因此直接以此签到天数获取今天签到奖励内容
        else:
            game_sign = 1
            signin_time = response["data"]["signinTime"] + 1  # 获取当月签到天数，今天未签到，因此需要+1天，获取今天签到后的天数，以此来获取对应的dayAwardId和签到奖励内容
        award_list = response["data"]["dayAward"]  # 当月奖励详情列表
        for i in range(len(award_list)):
            if award_list[i]["dayInPeriod"] == signin_time:
                periodId = award_list[i]["periodId"]
                dayAwardId = award_list[i]["id"]
                award = f"「{award_list[i]['awardName']}」*{award_list[i]['awardNum']}"
                break  # 找到当天的奖励了，直接中断for循环
        return game_sign, periodId, dayAwardId, award
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量dnabbs的值！")
    elif response["code"] == 500:
        raise SPException("失败", f"请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("失败", f"请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def do_signin_game(periodId, dayAwardId, award):
    """
    API：encourage/signin/signin
    进行二重螺旋游戏签到的API，需提前在皎皎角APP的签到页面绑定游戏角色
    """
    message = ""
    url = "https://dnabbs-api.yingxiong.com/encourage/signin/signin"
    data = {
        'signinType': "1",  # 未知用途
        'periodId': periodId,  # 可能是游戏签到月份的ID序号，在encourage/signin/show API的返回中“dayAward”项内的每一组数据，都有一个“periodId”项
        'dayAwardId': dayAwardId  # 签到奖励列表对应天数的ID，在encourage/signin/show API的返回中“dayAward”项内的每一组数据，都有一个“id”项
    }
    response = get_response(url, data, CONTENT_LENGTH_NUM["signInGame"])
    if response["code"] == 200:
        message += f"二重螺旋游戏签到成功：当月已签到 {response['data']['signinTimeNow']} 天，今天的游戏签到奖励是{award}。"
        return message
    elif response["code"] == 220:
        raise SPException("Cookie失效", "Cookie失效，请更新环境变量dnabbs的值！")
    elif response["code"] == 10000:
        #  重复签到，或periodId/dayAwardId不正确导致签到失败，填写正确的id重复签到也会返回同样的参数错误信息，所以无法确定具体是哪个情况
        message += f"二重螺旋游戏签到失败，或者今天已经签到过了，今天的游戏签到奖励是 {award}。"
        return message
    elif response["code"] == 500:
        raise SPException("失败", f"请求被拒绝，请重新尝试或检查日志！错误信息：{response['msg']}")
    else:
        raise SPException("失败", f"请求出现异常或被拒绝！Code {response['code']} - {response['msg']}")

def get_response(url, data, content_length):
    """
    返回处理为json的response
    """
    headers = {
        'User-Agent': "DoubleHelix/2 CFNetwork/3860.100.1 Darwin/25.0.0",
        'Host': "dnabbs-api.yingxiong.com",
        'version': "1.1.1",
        'lan': "en",
        'channel': "appstore",
        'Accept': "*/*",
        'devCode': UUID,
        'source': "ios",
        'Accept-Language': "zh-CN,zh-Hans;q=0.9",
        'Accept-Encoding': "gzip, deflate",
        'Ip': "192.168.3.101",
        'Content-Length': content_length,
        'Connection': "keep-alive",
        'Content-Type': "application/x-www-form-urlencoded; charset=utf-8",
        'model': "iPhone15,4",
        'osVersion': "26.0.1",
        'token': ACCOUNT
    }
    response = requests.post(url, data=data, headers=headers).json()
    return response

if __name__ == "__main__":
    """
    关于：社区每日任务 回复帖子5次
    此任务必须回复5个不同的帖子才会计数，且经测试，疑似每个帖子都只有一次计数机会，即非同一天回复同一个帖子时，此任务也不会计数
    由于以上种种限制，导致无法直接对官方水贴回复5次来完成任务，随机水贴回复其他玩家帖子可能出现不可预料的情况，因此放弃自动处理此任务
    """
    util.send_log(0, "二重螺旋·皎皎角 每日签到 - 开始执行")
    notify_content = ""
    if ACCOUNT is None:
        util.send_log(2, "缺少环境变量，请添加以下环境变量后再使用：dnabbs")
        util.send_notify("【缺少环境变量】二重螺旋·签到", "缺少环境变量，请添加以下环境变量后再使用：dnabbs（皎皎角账号Cookie）")
    else:
        try:
            restart_flag = True  # 是否需要重新运行，默认为True用于启动第一次循环执行
            attempt = 0  # 最多重复执行3次
            while restart_flag and attempt < 3:
                if attempt > 0:
                    util.send_log(1, f"社区交互任务执行出现意外的状况，开始重新执行，第{attempt + 2}次尝试中……")
                    notify_content += f"社区交互任务执行出现意外的状况，开始重新执行，第{attempt + 2}次尝试中……\n\n"
                restart_flag = False  # 循环开始将重新运行开关关闭
                attempt += 1  # 每次运行令运行次数计数+1，超出3次后不论是否成功都不再尝试
                # 获取用户皎皎角账号UID
                userId = get_dnabbs_userid()
                util.send_log(0, f"已获取用户皎皎角账号UID：{userId}。")
                notify_content += f"已获取用户皎皎角账号UID：{userId}。\n\n"
                time.sleep(2)
                # 获取用户今日任务完成情况，返回还需要进行多少次浏览帖子、点赞、社区签到、游戏签到、回复他人帖子次数的操作
                read, like, share, bbs_sign, comment = get_dnabbs_taskprocess(userId)
                time.sleep(2)
                # 直接使用获取本月游戏签到奖励列表API，其中也会有今天是否签到的data，实际有专门获取今天是否进行社区和游戏签到的API haveSignInNew，但直接使用此API可以同时获取到今天签到必须的表单值和签到奖励内容更方便
                game_sign, periodId, dayAwardId, award = get_signin_game_awards_list()
                util.send_log(0,  f"今日任务完成情况：点赞{' 已完成' if like == 0 else f'还需 {like} 次'}、浏览{' 已完成' if read == 0 else f'还需 {read} 次'}、分享{' 已完成' if share == 0 else f'还需 {share} 次'}、回复他人帖子{' 已完成' if comment == 0 else f'还需 {comment} 次'}、社区签到 {'已完成' if bbs_sign == 0 else '未完成'}、游戏签到 {'已完成' if game_sign == 0 else '未完成'}。")
                notify_content += f"今日任务完成情况：点赞{' 已完成' if like == 0 else f'还需 {like} 次'}、浏览{' 已完成' if read == 0 else f'还需 {read} 次'}、分享{' 已完成' if share == 0 else f'还需 {share} 次'}、回复他人帖子{' 已完成' if comment == 0 else f'还需 {comment} 次'}、社区签到 {'已完成' if bbs_sign == 0 else '未完成'}、游戏签到 {'已完成' if game_sign == 0 else '未完成'}。\n\n"
                time.sleep(2)
                # 如果需要浏览/点赞/分享，则获取帖子列表，返回1组帖子的id和发帖人id
                if read > 0 or like > 0 or share > 0:
                    postId, postUserId = get_dnabbs_new_formlist()
                    util.send_log(0, "已获取最新帖子列表，开始执行……")
                    time.sleep(2)
                    # 如果需要点赞次数不为0，则执行点赞
                    if like > 0:
                        for i in range(like):
                            restart_flag = do_unlike(postId, postUserId)  # 先取消点赞，防止这个帖子本身就被用户点过赞了导致第一次点赞不计入任务完成数中
                            if restart_flag:
                                util.send_log(1, f"执行第{i+1}次取消点赞操作时出现意外错误，可能是操作的帖子被删除了，重新开始社区交互任务执行流程……")
                                break  # 访问API返回非致命的错误，跳出循环并重新执行获取新的帖子ID，此处用于中止当前for循环
                            else:
                                util.send_log(0, f"执行第{i + 1}次取消点赞操作完成……")
                            time.sleep(1)
                            restart_flag = do_like(postId, postUserId)  # 执行点赞
                            if restart_flag:
                                util.send_log(1,f"执行第{i + 1}次点赞操作时出现意外错误，可能是操作的帖子被删除了，重新开始社区交互任务执行流程……")
                                break  # 访问API返回非致命的错误，跳出循环并重新执行获取新的帖子ID，此处用于中止当前for循环
                            else:
                                util.send_log(0, f"执行第{i + 1}次点赞操作完成……")
                            time.sleep(1)
                        util.send_log(0, f"点赞任务完成，执行了{like}次点赞帖子操作；")
                        notify_content += f"点赞任务完成，执行了{like}次点赞帖子操作；\n\n"
                    else:
                        util.send_log(0, "点赞任务已完成，不需要进行操作；")
                        notify_content += "点赞任务已完成，不需要进行操作；\n\n"
                    if restart_flag:
                        continue  # 访问API返回非致命的错误，跳出循环并重新执行获取新的帖子ID，此处用于中断后续代码运行并开始新的循环
                    # 如果需要浏览次数不为0，则执行浏览
                    if read > 0:
                        for i in range(read):
                            restart_flag = get_post_detail(postId)
                            if restart_flag:
                                util.send_log(1,f"执行第{i + 1}次浏览帖子操作时出现意外错误，可能是操作的帖子被删除了，重新开始社区交互任务执行流程……")
                                break  # 访问API返回非致命的错误，跳出循环并重新执行获取新的帖子ID，此处用于中止当前for循环
                            else:
                                util.send_log(0, f"执行第{i + 1}次浏览帖子操作完成……")
                            time.sleep(3)
                        util.send_log(0, f"浏览任务完成，执行了{read}次浏览帖子操作；")
                        notify_content += f"浏览任务完成，执行了{read}次浏览帖子操作；\n\n"
                    else:
                        util.send_log(0, "浏览任务已完成，不需要进行操作；")
                        notify_content += "浏览任务已完成，不需要进行操作；\n\n"
                    if restart_flag:
                        continue  # 访问API返回非致命的错误，跳出循环并重新执行获取新的帖子ID，此处用于中断后续代码运行并开始新的循环
                    # 如果需要分享次数不为0，则执行分享帖子
                    if share > 0:
                        for i in range(share):
                            restart_flag = do_share()
                            if restart_flag:
                                util.send_log(1, f"执行第{i + 1}次同步分享帖子任务进度操作时出现意外错误，重新开始社区交互任务执行流程……")
                                break  # 访问API返回非致命的错误，跳出循环并重新执行获取新的帖子ID，此处用于中止当前for循环
                            else:
                                util.send_log(0, f"执行第{i + 1}次同步分享帖子任务进度操作完成……")
                            time.sleep(3)
                        util.send_log(0, f"分享任务完成，执行了{share}次分享帖子操作；")
                        notify_content += f"分享任务完成，执行了{share}次分享帖子操作；\n\n"
                    else:
                        util.send_log(0, "分享任务已完成，不需要进行操作；")
                        notify_content += "分享任务已完成，不需要进行操作；\n\n"
                else:
                    util.send_log(0, "今日社区交互任务均已完成，不需要进行操作；")
                    notify_content += "今日社区交互任务均已完成，不需要进行操作；\n\n"
            if attempt == 2 and restart_flag:
                util.send_log(2, "社区交互任务执行出现意外的状况，已重复尝试3次仍未成功，放弃此部分任务的执行！")
                notify_content += "社区交互任务执行出现意外的状况，已重复尝试3次仍未成功，放弃此部分任务的执行！\n\n"

            # 如果需要社区签到，则执行签到
            if bbs_sign == 1:
                message_bbs_sign = do_signin_bbs()
                util.send_log(0, message_bbs_sign)
                notify_content += f"{message_bbs_sign}\n\n"
                time.sleep(5)
            else:
                util.send_log(0, "社区签到已完成，不需要进行操作；")
                notify_content += "社区签到已完成，不需要进行操作；\n\n"
            # 如果需要游戏签到，则执行签到
            if game_sign == 1:
                message_game_sign = do_signin_game(periodId, dayAwardId, award)
                util.send_log(0, message_game_sign)
                notify_content += f"{message_game_sign}\n\n"
                time.sleep(5)
            else:
                util.send_log(0, "游戏签到已完成，不需要进行操作；")
                notify_content += f"游戏签到已完成，不需要进行操作。今天的游戏签到奖励是 {award}；\n\n"
            # 全部完成，最终推送
            util.send_log(0, "二重螺旋·皎皎角 每日签到 - 执行完成")
            util.send_notify("二重螺旋·签到：已完成", notify_content)
        except SPException as e:
            # 主动抛出的异常，用于在出现非访问失败的问题时中断后续函数执行
            util.send_log(2, e.content)
            util.send_notify(f"【{e.title}】二重螺旋·签到", e.content)
        except requests.RequestException as e:
            # API访问失败的异常中断
            util.send_log(3, f"API请求失败 - {e}")
            util.send_notify("【失败】二重螺旋·签到", f"API请求失败，请查看日志！\n\n错误信息：{e}")
        except Exception as e:
            # 其他所有异常
            util.send_log(3, f"程序运行报错 - {e}")
            util.send_log(3, f"{traceback.format_exc()}")
            util.send_notify("【程序报错】二重螺旋·签到", f"程序运行报错，请查看日志！\n\n错误信息：{e}")