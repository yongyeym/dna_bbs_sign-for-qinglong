"""
任务名称
name: NGA社区 每日签到
定时规则
cron: 0 3 0 * * ?
"""

import traceback
import requests
from Utility.common import common_util as util
from Utility.common.common_util import get_md5

# 从环境变量获取Cookie
NGA_COOKIE, NGA_UID, NGA_CLIENT_CHECKSUM = util.get_os_env("nga_cookie", "nga_uid", "nga_client_checksum")
# 获取一个随机UUID的SHA256值作为设备标识符（IOS版本）
UUID_SHA256 = "iOS;" + util.get_sha256(util.get_uuid(4, False, True))
# 获取随机校验码，用于填充请求头中不会被检验的值
NGA_USER_INFO = "%25" + util.get_radom_string()
NGA_USER_INFO_CHECK = get_md5(NGA_USER_INFO)
WEBKIT_FORM_BOUNDARY = util.get_radom_string()

def doSign():
    """
    NGA社区 每日签到，主要执行部分
    """
    url = "https://ngabbs.com/nuke.php"
    cookie = (f"ngacn0comInfoCheckTime={util.get_timestamp(None, "s")}; "
              f"ngacn0comUserInfo={NGA_USER_INFO}; "
              f"ngacn0comUserInfoCheck={NGA_USER_INFO_CHECK}; "
              f"bbsmisccookies=%7B%7D; "
              f"access_token={NGA_COOKIE}; "
              f"access_uid={NGA_UID}")
    data = (f'------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name="__lib"\n\ncheck_in\n'
            f'------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name="__output"\n\n11\n'
            f'------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name="app_id"\n\n1100\n'
            f'------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name="device"\n\n{UUID_SHA256}\n'
            f'------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name="__act"\n\ncheck_in\n'
            f'------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name="access_uid"\n\n{NGA_UID}\n'
            f'------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name="access_token"\n\n{NGA_COOKIE}\n'
            f'------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name="__ngaClientChecksum"\n\n{NGA_CLIENT_CHECKSUM}\n'
            f'------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name="__inchst"\n\nUTF-8\n'
            f'------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}--\n')
    headers = {
        'Host': 'ngabbs.com',
        'X-USER-AGENT': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148  NGA_skull/10.1.36',
        'Accept': '*/*',
        'Sec-Fetch-Site': 'same-origin',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Sec-Fetch-Mode': 'cors',
        'Content-Type': f'multipart/form-data; boundary=----WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}',
        'Origin': 'https://ngabbs.com',
        'Content-Length': '1096',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148  NGA_skull/10.1.36',
        'Referer': 'https://ngabbs.com/misc/mission/mission.php',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Cookie': cookie
    }

    try:
        response = requests.post(url,  headers=headers, data=data)
        if response.status_code == 200:
            response_data = response.json()
            print(response_data)
            if "data" in response_data:
                if "签到成功" in response_data["data"][0]:
                    sum = response_data["data"][1]["sum"]
                    continued = response_data["data"][1]["continued"]
                    util.send_log(0, f"NGA社区 今日签到成功。当前连续签到 {continued} 天，累计签到 {sum} 天。")
                    util.send_notify("NGA社区·签到：已完成", f"NGA社区 今日签到成功。\n\n当前连续签到 {continued} 天，累计签到 {sum} 天。")
                else:
                    util.send_log(1, f"出现了未知错误,错误信息：{response_data['data'][0]}")
                    util.send_notify("【失败】NGA社区·签到", f"出现了未知错误，请查看日志！\n\n错误信息：{response_data['data'][0]}")
            elif "error" in response_data:
                if "你今天已经签到了" in response_data["error"][0]:
                    util.send_log(0, "今天已经签到过，无需签到。")
                    util.send_notify("NGA社区·签到：已签到", "今天已经签到过，无需签到。")
                elif "你必须先登录论坛" in response_data["error"][0]:
                    util.send_log(2, "NGA账号Cookie已过期，无法签到。请更新环境变量nga_cookie的值！")
                    util.send_notify("【Cookie过期】NGA社区·签到", "NGA账号Cookie已过期，无法签到。需要更新环境变量nga_cookie的值！")
                elif "CLIENT ERROR" in response_data["error"][0]:
                    util.send_log(2, "NGA客户端校验码已过期/不适配/非IOS端抓包的校验码，无法通过NGA服务器验证。请更新环境变量nga_client_checksum的值！")
                    util.send_notify("【Cookie过期】NGA社区·签到", "NGA客户端校验码已过期/不适配/非IOS端抓包的校验码，无法NGA服务器验证。需要更新环境变量nga_client_checksum的值！")
                else:
                    util.send_log(1, f"出现了未知错误,错误信息：{response_data['error']}")
                    util.send_notify("【失败】NGA社区·签到", f"出现了未知错误，请查看日志！\n\n错误信息：{response_data['error']}")
        else:
            util.send_log(1, f"出现了未知错误,状态码： {response.status_code}")
            util.send_notify("【失败】NGA社区·签到", f"出现了未知错误，请查看日志！\n\n状态码：{response.status_code}")
    except requests.RequestException as e:
        util.send_log(3, f"API请求失败 - {e}")
        util.send_notify("【失败】NGA社区·签到", f"API请求失败，请查看日志！\n\n错误信息：{e}")

if __name__ == "__main__":
    util.send_log(0, "NGA社区 每日签到 - 开始执行")
    value_check = ""  # 存储环境变量为空的变量名用于推送通知正文内容
    if NGA_COOKIE is None:
        value_check += "【nga_cookie】"
    elif NGA_UID is None:
        value_check += "【nga_uid】"
    elif NGA_CLIENT_CHECKSUM is None:
        value_check += "【nga_client_checksum】"
    if value_check == "":
        try:
            doSign()
        except Exception as e:
            util.send_log(3, f"程序运行报错 - {e}")
            util.send_log(3, f"{traceback.format_exc()}")
            util.send_notify("【程序报错】NGA社区·签到", f"程序运行报错，请查看日志！\n\n错误信息：{e}")
    else:
        util.send_log(2, f"缺少环境变量，请添加以下环境变量后再使用：{value_check}")
        util.send_notify("【缺少环境变量】NGA社区·签到", f"缺少环境变量，请添加以下环境变量后再使用：{value_check}")