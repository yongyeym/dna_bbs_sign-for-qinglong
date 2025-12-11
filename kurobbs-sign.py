"""
任务名称
name: 鸣潮·库街区 每日签到
定时规则
cron: 0 3 0 * * ?
"""

import requests
import json
from Utility.common import common_util as util

# 从环境变量获取Cookie
ACCOUNT = util.get_os_env("kurobbs")[0]

def doSign():
    url = "https://api.kurobbs.com/encourage/signIn/v2"
    params = {
        'userId': "27914240",  # 库街区用户ID
        'roleId': "103701444",  # 鸣潮游戏ID
        'gameId': "3",  # 鸣潮在库街区游戏ID编号
        'serverId': "76402e5b20be2c39f095a152090afddc",  # 鸣潮在库街区国服区域编号
        'reqMonth': util.get_format_datetime()["month"]  # 获取当前月份数字，不足2位则前面补0
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
        'Accept-Encoding': "gzip, deflate",
        'Content-Type': "application/x-www-form-urlencoded",
        'Accept': "application/json, text/plain, */*",
        'pragma': "no-cache",
        'cache-control': "no-cache",
        'sec-ch-ua': "\"Chromium\";v=\"124\", \"Android WebView\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
        'source': "h5",
        'devcode': "111.181.85.154, Mozilla/5.0 (Linux; Android 14; 22081212C Build/UKQ1.230917.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/124.0.6367.179 Mobile Safari/537.36 Kuro/2.2.0 KuroGameBox/2.2.0",
        'sec-ch-ua-platform': "\"Android\"",
        'origin': "https://web-static.kurobbs.com",
        'x-requested-with': "com.kurogame.kjq",
        'sec-fetch-site': "same-site",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        'priority': "u=1, i",
        'token': ACCOUNT
    }

    try:
        response = json.loads(requests.post(url, params=params, headers=headers).text)
        if response['code'] == 200 and "请求成功" in response['msg']:
            util.send_log(0, "鸣潮·库街区 今日签到成功。")
            util.send_notify("鸣潮·签到：已完成", "鸣潮·库街区 今日签到成功。")
        elif response['code'] == 1511 and "请勿重复签到" in response['msg']:
            util.send_log(0, "今天已经签到过，无需签到。")
            util.send_notify("鸣潮·签到：已签到", "今天已经签到过，无需签到。")
        elif response['code'] == 220 and "登录已过期，请重新登录" in response['msg']:
            util.send_log(2, "库街区Cookie已过期，无法签到。请更新环境变量kurobbs的值！")
            util.send_notify("【Cookie过期】鸣潮·签到", "库街区Cookie已过期，无法签到。需要更新环境变量kurobbs的值！")
        else:
            util.send_log(1, f"出现了未知错误： {response['code']} - {response['msg']}")
            util.send_notify("【失败】鸣潮·签到",
                             f"出现了未知错误，请查看日志！\n\n状态码与错误信息：{response['code']} - {response['msg']}")
    except requests.RequestException as e:
        util.send_log(3, f"API请求失败 - {e}")
        util.send_notify("【失败】鸣潮·签到", f"API请求失败，请查看日志！\n\n错误信息：{e}")

if __name__ == "__main__":
    util.send_log(0, "鸣潮·库街区 每日签到 - 开始执行")
    if ACCOUNT is None:
        util.send_log(2, "缺少环境变量，请添加以下环境变量后再使用：kurobbs")
        util.send_notify("【缺少环境变量】鸣潮·签到","缺少环境变量，请添加以下环境变量后再使用：kurobbs（库街区账号Cookie）")
    else:
        try:
            doSign()
        except Exception as e:
            util.send_log(3, f"程序运行报错 - {e}")
            util.send_notify("【程序报错】鸣潮·签到", f"程序运行报错，请查看日志！\n\n错误信息：{e}")