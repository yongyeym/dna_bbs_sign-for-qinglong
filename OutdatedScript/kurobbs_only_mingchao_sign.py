"""
任务名称
name: 鸣潮·游戏 每日签到
定时规则
cron: 30 10 0 * * ?
"""

import traceback
import requests
import json
from Utility.common import common_util as util

# 从本地配置文件获取是否使用本地Cookie
USE_LOCAL_COOKIE = util.get_config_env("use_local_cookie")[0] == "1"
# 从环境变量或本地ini文件获取Cookie和UID
ACCOUNT, USER_ID = util.get_config_env("kurobbs", "kuro_uid") if USE_LOCAL_COOKIE else util.get_os_env("kurobbs", "kuro_uid")

def doSign() -> None:
    """
    仅进行鸣潮游戏签到的脚本，老版本脚本留档，不再更新
    需要在下方 'roleId': 后面填入自己的游戏UID
    且与新版本签到脚本一样配置kurobbs、kuro_uid两个环境变量
    本版本脚本的URL请求头headers参数来自GitHub项目鸣潮Tool工具箱中的签到代码部分
    """
    url = "https://api.kurobbs.com/encourage/signIn/v2"
    params = {
        'userId': USER_ID,  # 库街区账号UID
        'roleId': "此处双引号内填写你的游戏UID！",  # 鸣潮角色UID
        'gameId': "3",  # 鸣潮在库街区游戏ID编号
        'serverId': "76402e5b20be2c39f095a152090afddc",  # 鸣潮国服在库街区的服务器编号，若为鸣潮官服则不用修改，其他服务器未测试过
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
            util.send_log("鸣潮·库街区 今日签到成功。", "info")
            util.send_notify("鸣潮·签到：已完成", "鸣潮·库街区 今日签到成功。")
        elif response['code'] == 1511 and "请勿重复签到" in response['msg']:
            util.send_log("今天已经签到过，无需签到。", "info")
            util.send_notify("鸣潮·签到：已签到", "今天已经签到过，无需签到。")
        elif response['code'] == 220 and "登录已过期，请重新登录" in response['msg']:
            util.send_log("库街区Cookie已过期，无法签到。请更新环境变量kurobbs的值！", "error")
            util.send_notify("【Cookie过期】鸣潮·签到", "库街区Cookie已过期，无法签到。需要更新环境变量kurobbs的值！")
        else:
            util.send_log(f"出现了未知错误： {response['code']} - {response['msg']}", "warning")
            util.send_notify("【失败】鸣潮·签到",
                             f"出现了未知错误，请查看日志！\n\n状态码与错误信息：{response['code']} - {response['msg']}")
    except requests.RequestException as e:
        util.send_log(f"API请求失败 - {e}", "critical")
        util.send_notify("【失败】鸣潮·签到", f"API请求失败，请查看日志！\n\n错误信息：{e}")

if __name__ == "__main__":
    util.send_log("鸣潮·库街区 每日签到 - 开始执行", "info")
    value_check = ""
    if ACCOUNT is None:
        value_check += "【kurobbs】"
    if USER_ID is None:
        value_check += "【kuro_uid】"
    if value_check == "":
        try:
            doSign()
        except Exception as e:
            util.send_log(f"程序运行报错 - {e}", "critical")
            util.send_log(f"{traceback.format_exc()}", "critical")
            util.send_notify("【程序报错】鸣潮·签到", f"程序运行报错，请查看日志！\n\n错误信息：{e}")
    else:
        util.send_log(f"缺少环境变量配置！需要添加环境变量：{value_check}", "error")
        util.send_notify("【缺少环境变量】鸣潮·签到", f"缺少环境变量，请添加以下环境变量后再使用：{value_check}")