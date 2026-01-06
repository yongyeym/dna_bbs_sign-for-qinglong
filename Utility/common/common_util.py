import os
import configparser
import logging
import random
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Optional, NoReturn
from Utility import notify

# 配置文件相关
CONFIG_DIR = Path(__file__).parent.parent.parent / "Config"
CONFIG_PATH = CONFIG_DIR / "config.ini"
DEFAULT_CONFIG = {
    "use_local_cookie": "0",
    "url_timeout": "10",
    "url_retry_times": "5",
    "url_retry_interval": "5",
}
COOKIE_CONFIG = {
    "dnabbs": "",
    "kurobbs": "",
    "kuro_uid": "",
    "nga_cookie": "",
    "nga_uid": "",
    "nga_client_checksum": "",
}

def get_os_env(*args: str) -> tuple[str | None, ...]:
    """
    获取对应的环境变量值，并去除前后空格，可一次获取多个环境变量
    :param args：环境变量的Key，可以是多个
    :return 返回元组，可以使用一个变量接收（只获取一个变量时可直接使用下标[0]来获取值），也可以分别赋予多个变量单独接收，如果不存在此环境变量，则对应位置的值返回None。
    """
    return tuple(
        value.strip() if value is not None else None
        for value in (os.getenv(str(arg)) for arg in args)
    )

def get_config_env(*args: str, section: str = "DEFAULT") -> tuple[str | None, ...]:
    """
    获取本地的配置文件Config/config.ini中的变量值，并去除前后空格，可一次获取多个环境变量
    :param args：变量的Key，可以是多个
    :param section: 配置文件的section，需要使用section = "值" 来指定，否则会被当作key来查询；若未传入此参数或传入的值不存在于配置文件中，则使用默认值DEFAULT
    :return 返回元组，可以使用一个变量接收（只获取一个变量时可直接使用下标[0]来获取值），也可以分别赋予多个变量单独接收，如果不存在此环境变量，则对应位置的值返回None。
    """
    config = configparser.ConfigParser()
    # 检查配置文件是否存在，不存在则创建此文件并填入默认值
    if not os.path.exists(CONFIG_PATH):
        if not write_config_init():
            return (None,) * len(args)  # 创建默认配置文件失败，返回包含与传入参数数量相同数量的None的元组
    # 读取配置文件，若读取失败则返回包含与传入参数数量相同数量的None的元组
    try:
        config.read(CONFIG_PATH)
    except configparser.Error:
        return (None,) * len(args)
    # 检查是否有传入的section，若不存在则使用默认的DEFAULT查询
    if str(section) not in config:
        section = "DEFAULT"
    # 读取每个key的值，去除左右空格，如果不存在或为空字符串则返回None
    return tuple((config[str(section)].get(str(arg), "").strip() or None) for arg in args)

def write_config_init() -> bool:
    """
    初始化配置文件，填入默认配置
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)  # 确保目录存在
    config = configparser.ConfigParser()
    config['DEFAULT'] = DEFAULT_CONFIG
    config['COOKIE'] = COOKIE_CONFIG
    try:
        with open(CONFIG_PATH, 'w') as f:
            config.write(f)
    except IOError as e:
        send_log(f"无法创建或写入配置文件{CONFIG_PATH}！错误信息:{e}", "error")
        return False
    send_log(f"已初始化配置文件{CONFIG_PATH}！", "info")
    return True

def write_config_env(key: str, value: str = "", section: str = "DEFAULT") -> bool:
    """
    写入配置文件Config/config.ini中的变量值
    :param key: 需要写入配置文件的Key键名
    :param value: 需要写入配置文件的key对应的值，默认为空字符串（None）
    :param section: 配置文件的分组，默认为DEFAULT
    :return: 是否成功写入
    """
    # 处理传入的值，防止传入错误类型的值导致报错
    if key is None:
        return False
    if value is None:
        value = ""
    if section is None:
        section = "DEFAULT"
    key = str(key)
    value = str(value)
    section = str(section)
    # 确保目录存在
    os.makedirs(CONFIG_DIR, exist_ok=True)
    config = configparser.ConfigParser()
    # 配置文件不存在且创建默认配置文件失败，直接返回False
    if not os.path.exists(CONFIG_PATH):
        if not write_config_init():
            return False
    try:
        config.read(CONFIG_PATH) # 读取配置文件原有内容
        if section not in config:
            config.add_section(section) # 如果不存在此section，则添加
        config.set(section, key, value)
        with open(CONFIG_PATH, 'w') as f:
            config.write(f)
    except configparser.Error:
        send_log(f"[{section}] {key} = {value} 无法读取配置文件{CONFIG_PATH}！", "error")
        return False
    except IOError as e:
        send_log(f"[{section}] {key} = {value} 写入配置文件{CONFIG_PATH}失败！错误信息:{e}", "error")
        return False
    send_log(f"[{section}] {key} = {value} 已写入配置文件！", "info")
    return True

def get_timestamp(input_time: Optional[Union[datetime, str]] = None, type: str = "ms") -> int:
    """
    获取当前时间戳
    :param type:时间戳精度，默认为毫秒级13位数字，反之为秒级10位数字
    :param input_time:需要转时间戳的时间，默认为当前系统时间
    :return 返回时间戳
    """
    if input_time is None:
        input_time = datetime.now()
    elif not isinstance(input_time, datetime):
        try:
            #  使用ISO标准格式化字符串为datetime
            input_time = datetime.fromisoformat(input_time)
        except ValueError:
            try:
                #  使用自定义的格式，格式化字符串为datetime
                input_time = datetime.strptime(input_time, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                raise ValueError(f"无法转化为时间戳，传入的字符串无法解析为时间日期: {input_time}") from e
    return int(input_time.timestamp()*1000 if type == "ms" else input_time.timestamp())

def get_format_timestamp(timestamp: int, format: str = "%Y年%m月%d日 %H:%M:%S") -> str:
    """
    将时间戳格式化为时间日期的可视化文本
    :param timestamp:时间戳
    :param format:格式化的格式，默认为 年月日 时分秒
    :return 返回格式化后的时间日期文本
    """
    return datetime.fromtimestamp(int(timestamp)).strftime(format)

def get_format_datetime(input_time: Optional[Union[datetime, str]] = None) -> Dict[str, str]:
    """
    获取格式化后的时间日期
    :param input_time:需要格式化的时间日期原数据，默认为当前系统时间
    :return 返回包含所有时间格式的字典
    """
    if input_time is None:
        input_time = datetime.now()
    elif not isinstance(input_time, datetime):
        try:
            #  使用ISO标准格式化字符串为datetime
            input_time = datetime.fromisoformat(input_time)
        except ValueError:
            try:
                #  使用自定义的格式，格式化字符串为datetime
                input_time = datetime.strptime(input_time, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                raise ValueError(f"无法转化为时间戳，传入的字符串无法解析为时间日期: {input_time}") from e
    date = input_time.strftime("%Y年%m月%d日")  #处理为 年月日 格式
    time = input_time.strftime("%H:%M:%S")  #处理为 时分秒 格式
    datetime_all = input_time.strftime("%Y年%m月%d日 %H:%M:%S")  #处理为 年月日 时分秒 格式
    now_weekday = f"{['星期一','星期二','星期三','星期四','星期五','星期六','星期日'][input_time.weekday()]}"  #处理为 星期 格式
    now_year = f"{input_time.year}"  # 处理为 当前年份 格式
    now_month = "{:02d}".format(input_time.month)  #处理为 当前月份 格式，且不足2位时前面补0
    now_day = "{:02d}".format(input_time.day)  # 处理为 当前日期 格式，且不足2位时前面补0
    return {"date": date, "time": time, "datetime": datetime_all, "weekday": now_weekday, "complete_time": datetime_all + " " + now_weekday, "year": now_year, "month": now_month, "day": now_day}  #返回包含所有格式的字典

def get_format_process(process_num) -> str:
    """
    对小数表示的百分比数据进行格式化处理，处理为保留小数点后两位的百分比显示结果
    """
    return str(int(float(process_num) * 10000) / 100) + "%"  #将原小数*10000再转整型，去除多余的小数点后位数，再除以100，得到有小数点后2位的百分比显示结果

def get_uuid(uuid_type: int = 4, need_upper: bool = True, need_hex: bool = False) -> str:
    """
    获取一个通用唯一标识符UUID，英文字母大写
    get_uuid返回的是一般格式的UUID，如 8BC5D95B-F573-52F5-065B-34F37C700956
    get_uuid_hex返回的是去掉UUID的-之后的UUID，如 8BC5D95BF57352F5065B34F37C700956

    uuid版本：
    UUID1基于时间戳、MAC地址、随机数
    UUID3基于命名空间和名称的MD5
    UUID4基于随机数
    UUID5基于命名空间和名称的SHA-1

    uuid命名空间：
    NAMESPACE_DNS基于DNS地址
    NAMESPACE_URL基于URL网址
    NAMESPACE_OID基于ISO OID
    NAMESPACE_X500基于X.500 DN

    :param uuid_type：使用哪一种UUID算法 1/3/4/5，传入参数错误或未传入时使用UUID4
    :param need_upper：是否需要大写输出，默认为是
    :param need_hex：是否需要转为32位十六进制字符串，即去掉UUID中的间隔符横杠-，默认为否
    :return 返回生成的随机UUID字符串，默认为UUID4生成的标准格式大写字符串
    """
    if uuid_type == 1:
        new_uuid = uuid.uuid1()
    elif uuid_type == 3:
        new_uuid = uuid.uuid3(uuid.NAMESPACE_URL, "example.com")  # 暂不考虑使用此方法，此处仅写出使用方式
    elif uuid_type == 4:
        new_uuid = uuid.uuid4()
    elif uuid_type == 5:
        new_uuid = uuid.uuid5(uuid.NAMESPACE_URL, "example.com")  # 暂不考虑使用此方法，此处仅写出使用方式
    else:
        new_uuid = uuid.uuid4()
    if need_hex:
        new_uuid = new_uuid.hex
    new_uuid = str(new_uuid)  # 进行字符串化
    if need_upper:
        new_uuid.upper()
    return new_uuid

def get_md5(content: str) -> str:
    """
    :param content:需要计算MD5的文本
    :return:返回文本的MD5
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def get_sha1(content: str) -> str:
    """
    :param content:需要计算SHA1的文本
    :return:返回文本的SHA1
    """
    return hashlib.sha1(content.encode('utf-8')).hexdigest()

def get_sha256(content: str) -> str:
    """
    :param content:需要计算SHA256的文本
    :return:返回文本的SHA256
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def get_radom_string(length: int = 16) -> str:
    """
    获取指定长度的随机字符串
    :param length:随机字符串的长度，默认16位
    :return:返回随机字符串
    """
    random_list = [chr(i) for i in range(ord('a'), ord('z'))]
    random_list += [chr(i) for i in range(ord('A'), ord('Z'))]
    random_list += [chr(i) for i in range(ord('0'), ord('9'))]
    random_list = ''.join(random_list)
    return ''.join(random.choice(random_list) for _ in range(length))

def send_notify(title: str, content: str = "无详细信息，请查看日志！") -> NoReturn:
    """
    发送通知推送，使用青龙自带的notify服务，需要在青龙配置中提前配置好任意推送渠道的key
    :param title：标题
    :param content：详细内容
    """
    now_time = get_format_datetime()["datetime"]
    text = f"结束时间：\n\n{now_time}\n\n运行详情：\n\n{content}"
    notify.send(title, text)

#  初始化logging日志配置
logging.basicConfig(
    level=logging.INFO,  # 设置日志输出级别
    format='%(asctime)s | %(levelname)s | %(message)s',  # 设置日志输出内容的格式化（日期时间 | 级别 | 信息）
    datefmt='%Y年%m月%d日 %H:%M:%S',  # 设置日志的时间日期显示格式
    encoding = "utf-8"
)

def send_log(content: str, log_level: str | int = "info") -> None:
    """
    发送Log日志。默认输出INFO及以上级别日志
    :param log_level：日志级别，默认info：info/0 信息 | warning/1 警告 | error/2 错误 | critical/3 致命错误 | debug/-1 DEBUG
    :param content：详细日志内容
    """
    log_level = str(log_level).lower().strip().split()  # 对传入的日志级别参数处理，转换为全小写、去除前后空格、以空格分割字符串
    if "info" in log_level or "0" in log_level:
        logging.info(content)
    elif "warning" in log_level or "1" in log_level:
        logging.warning(content)
    elif "error" in log_level or "2" in log_level:
        logging.error(content)
    elif "critical" in log_level or "3" in log_level:
        logging.critical(content)
    elif "debug" in log_level or "-1" in log_level:
        logging.debug(content)
    else:
        logging.info(content)  # 无法匹配传入的日志级别参数时默认输出info日志

def send_log_debug(content: str) -> None:
    """
    发送Debug级别Log日志打印到控制台
    :param content：详细日志内容
    """
    logger = logging.getLogger('debug_logger')
    logger.setLevel(logging.DEBUG)
    logger.debug(content)

class SPException(Exception):
    """
    主动抛出异常，用于中断后续无效的函数执行并直接进行最后的通知推送
    使用 raise SPException("title", "content") 主动抛出
    """
    def __init__(self, title: str = "运行失败", content: str = "请查看日志！") -> None:
        self.title = title
        self.content = content
        super().__init__(self.title)
    def __str__(self) -> str:
        e2str = f"【{self.title}】\n\n错误详情为：" + self.content  # 定义直接输出e时的显示文本
        return e2str