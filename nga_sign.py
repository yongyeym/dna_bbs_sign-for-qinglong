"""
任务名称
name: NGA社区 每日签到
定时规则
cron: 0 3 0 * * ?
"""
import time
import traceback
import requests
from Utility.common import common_util as util

# 获取一个随机UUID的SHA256值作为设备标识符（IOS版本）
UUID_SHA256 = "iOS;" + util.get_sha256(util.get_uuid(4, False, True))
# 获取随机校验码，用于填充请求头中不会被检验的值
NGA_USER_INFO = "%25" + util.get_radom_string()
NGA_USER_INFO_CHECK = util.get_md5(NGA_USER_INFO)
WEBKIT_FORM_BOUNDARY = util.get_radom_string()
# 从本地配置文件获取是否使用本地Cookie
USE_LOCAL_COOKIE = util.get_config_env("use_local_cookie")[0] == "1"
# 从本地配置文件获取URL访问失败重试的相关配置
URL_TIMEOUT, URL_RETRY_TIMES, URL_RETRY_INTERVAL = map(lambda x: int(x) if x.isdigit() else 0, util.get_config_env("url_timeout", "url_retry_times", "url_retry_interval"))
# 从环境变量或本地ini文件获取Cookie、UID、CLIENT_CHECKSUM
NGA_COOKIE, NGA_UID, NGA_CLIENT_CHECKSUM = util.get_config_env("nga_cookie", "nga_uid", "nga_client_checksum", section="COOKIE") if USE_LOCAL_COOKIE else util.get_os_env("nga_cookie", "nga_uid", "nga_client_checksum")

def doSign() -> None:
    """
    NGA社区 每日签到，主要执行部分
    """
    url = "https://ngabbs.com/nuke.php"
    try:
        response_data = get_response(url)
        if "data" in response_data:
            if "签到成功" in response_data["data"][0]:
                sum = response_data["data"][1]["sum"]
                continued = response_data["data"][1]["continued"]
                util.send_log(f"NGA社区 今日签到成功。当前连续签到 {continued} 天，累计签到 {sum} 天。", "info")
                util.send_notify("NGA社区·签到：已完成", f"NGA社区 今日签到成功。\n\n当前连续签到 {continued} 天，累计签到 {sum} 天。")
            else:
                util.send_log(f"出现了未知错误,错误信息：{response_data['data'][0]}", "warning")
                util.send_notify("【失败】NGA社区·签到",f"出现了未知错误，请查看日志！\n\n错误信息：{response_data['data'][0]}")
        elif "error" in response_data:
            if "你今天已经签到了" in response_data["error"][0]:
                util.send_log("今天已经签到过，无需签到。", "info")
                util.send_notify("NGA社区·签到：已完成", "今天已经签到过，无需签到。")
            elif "你必须先登录论坛" in response_data["error"][0]:
                util.send_log("NGA账号Cookie已过期，无法签到。请更新环境变量【nga_cookie】！", "error")
                util.send_notify("【Cookie过期】NGA社区·签到",
                                 "NGA账号Cookie已过期，无法签到。请更新环境变量【nga_cookie】！")
            elif "CLIENT ERROR" in response_data["error"][0]:
                util.send_log("NGA客户端校验码已过期/不适配/非IOS端抓包的校验码，无法通过NGA服务器验证。请更新环境变量【nga_client_checksum】！", "error")
                util.send_notify("【Cookie过期】NGA社区·签到","NGA客户端校验码已过期/不适配/非IOS端抓包的校验码，无法NGA服务器验证。请更新环境变量【nga_client_checksum】！")
            else:
                util.send_log(f"出现了未知错误,错误信息：{response_data['error']}", "error")
                util.send_notify("【失败】NGA社区·签到", f"出现了未知错误，请查看日志！\n\n错误信息：{response_data['error']}")
    except requests.RequestException as e:
        util.send_log(f"API请求失败 - {e}", "critical")
        util.send_notify("【失败】NGA社区·签到", f"API请求失败，请查看日志！\n\n错误信息：{e}")

def get_response(url) -> any:
    """
    返回处理为json的response
    :return: 返回处理为json的response
    """
    cookie = (f"ngacn0comInfoCheckTime={util.get_timestamp(None, 's')}; "
              f"ngacn0comUserInfo={NGA_USER_INFO}; "
              f"ngacn0comUserInfoCheck={NGA_USER_INFO_CHECK}; "
              f"bbsmisccookies=%7B%7D; "
              f"access_token={NGA_COOKIE}; "
              f"access_uid={NGA_UID}")
    data = (
        f"------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name='__lib'\n\ncheck_in\n"
        f"------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name='__output'\n\n11\n"
        f"------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name='app_id'\n\n1100\n"
        f"------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name='device'\n\n{UUID_SHA256}\n"
        f"------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name='__act'\n\ncheck_in\n"
        f"------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name='access_uid'\n\n{NGA_UID}\n"
        f"------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name='access_token'\n\n{NGA_COOKIE}\n"
        f"------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name='__ngaClientChecksum'\n\n{NGA_CLIENT_CHECKSUM}\n"
        f"------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}\nContent-Disposition: form-data; name='__inchst'\n\nUTF-8\n"
        f"------WebKitFormBoundary{WEBKIT_FORM_BOUNDARY}--\n")
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
    last_exception = None
    for i in range(URL_RETRY_TIMES):
        try:
            response = requests.post(url, data=data, headers=headers, timeout=URL_TIMEOUT)
            response.raise_for_status()  # 如果响应状态码不是200，主动抛出异常进行重试访问
            return response.json()
        except requests.RequestException as e:
            last_exception = e
            util.send_log(f"URL访问失败（第{i + 1}次），5秒后重试……", "warning")
            if i < URL_RETRY_TIMES:  # 失败时，等待指定秒后重试请求
                time.sleep(URL_RETRY_INTERVAL)
    raise last_exception  # 重试多次都失败时抛出最后一次失败时的异常，在主程序部分捕获，用于返回API访问失败导致程序运行失败的提示

if __name__ == "__main__":
    util.send_log("NGA社区 每日签到 - 开始执行", "info")
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
            util.send_log(f"程序运行报错 - {e}", "critical")
            util.send_log(f"{traceback.format_exc()}", "critical")
            util.send_notify("【程序报错】NGA社区·签到", f"程序运行报错，请查看日志！\n\n错误信息：{e}")
    else:
        util.send_log(f"缺少环境变量，请添加以下环境变量后再使用：{value_check}", "error")
        util.send_notify("【缺少环境变量】NGA社区·签到", f"缺少环境变量，请添加以下环境变量后再使用：{value_check}")