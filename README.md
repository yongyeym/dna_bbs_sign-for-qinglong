# 青龙面板自动脚本 AutoSign_QingLong
### 个人NAS的青龙面板自用脚本
##### 因测试有限，可能会有意料之外的Bug，遇到对应问题后会修复。
##### ⚠ 请勿大范围传播，如有需要可自由使用或改造本仓库代码 ⚠
1. 青龙面板添加依赖：Python3的Requests包；
2. 使用青龙面板自带的推送服务notify.py，需要在青龙面板-配置文件中添加自己需要推送的APP的Key，若不需要推送则不填；
3. 复制Config/config-template.ini配置文件模板，改名为config.ini放在同文件夹内，若无此配置文件运行任意脚本时会自动生成并填入默认设置；
4. 青龙面板添加需要的环境变量，也可以改为使用脚本目录下Config/config.ini中[COOKIE]分组内的值（需启用此功能，将[DEFAULT]中的use_local_cookie = 0改为1）；
5. 通用代码单独放在了一个py文件中，青龙面板推送py文件也被我修改了默认文件位置，文件位于Utility目录下；全部脚本都需要依赖这两个py文件，请保证文件存在且路径正确，使用非git方式手动更新时注意也要更新这两个文件；
---
可使用下方代码创建本仓库的青龙订阅：
```
ql repo https://github.com/yongyeym/AutoSign_QingLong.git
```
---

<details>
  <summary>【点击这里查看：Config/config.ini配置文件说明】</summary>

存放所有脚本通用的配置，可根据需要修改
```
[DEFAULT]
# 是否启用此配置文件内的COOKIE，填写1则启用，填写任何其他值则不启用
use_local_cookie = 0

# URL访问超时设置（秒）
url_timeout = 10

# URL重试次数（每一次URL访问都会单独计算次数）
url_retry_times = 5

# URL每次重试访问的间隔（秒）
url_retry_interval = 5
```
存放各个脚本需要获取的变量，默认不启用
```
[COOKIE]

# 鸣潮·库街区
kurobbs = 
kuro_uid =

# NGA
nga_cookie = 
nga_uid = 
nga_client_checksum =

#异环·塔吉多
tajiduo=

```

</details>

---
```
task yongyeym_AutoSign_QingLong_main/nga_sign.py
```
#### NGA社区 每日签到
##### 仅适配IOS端，需要抓包IOS版APP
##### ⚠ 目前NGA客户端验证参数ngaClientChecksum无法使用随机生成值，且不同平台的值格式不同，目前仅做IOS版适配，需要抓包获取 ⚠
1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量：nga_uid、nga_cookie、nga_client_checksum
3. 从[NGA社区PC端网页](https://bbs.nga.cn/)或APP抓包获取cookie中部分内容，从F12网络选项卡中，找到nuke.php请求header中的cookie：
   * nga_uid：账号的UID，可以直接去个人主页找到，也可以在PC版cookie中的ngaPassportUid，移动版cookie中的access_uid中找到；
   * nga_cookie：账号的Cookie，在PC版cookie中的ngaPassportCid，移动版cookie中的access_token中看到；
4. 使用IOS抓包工具，抓取IOS版恩基爱论坛APP，从请求头表单中找到__ngaClientChecksum的值：
   * nga_client_checksum：NGA的IOS版客户端校验码，IOS版本是以/uid结尾的字符串；

#### 更新日志：


2025/12/12：
* 初始版本发布
---
```
task yongyeym_AutoSign_QingLong_main/kurobbs_sign.py
```
#### 鸣潮&库街区 国服 每日游戏签到
##### 库街区每日签到、鸣潮每日签到、库街区社区每日任务（点赞、浏览、分享）
##### 只对鸣潮处理，没有战双帕弥什的游戏签到，但理论上只需要把各参数里的gameId从3改成2即可
##### 必须手动设置库街区账号的UID，获取账号信息的API需要传入此UID进行查询，获取社区UID的API只有社区APP登录账号的API会返回，因此无法自动获取
1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量：kurobbs，可从[库街区PC端网页](http://www.kurobbs.com/mc/home/9)获取账号token（ey开头）；
3. 青龙面板添加环境变量：kuro_uid，库街区账号的UID，可在库街区个人页找到，不是游戏角色UID；

#### 更新日志：


2026/05/21：
* 更新帖子被删除时API返回的错误码，使其能正常进入帖子被删除重新获取一个帖子的流程

2026/05/21：
* 原API请求头更新导致无法使用，会返回Token过期，因此进行了更新。
* 请求头参数有大量修改，可能会有各种问题发生，还需要长期进行测试确认。

2026/04/21：
* 修复几处不影响使用的错别字。

2026/02/04：
* 因新脚本运行多周未出现任何问题，老版本脚本/old_files/kurobbs_only_mingchao_sign.py将不再更新，但仍保留，如有需要可继续使用，不保证后续兼容性。

2025/12/12：
* 初始版本发布，代码由二重螺旋签到脚本代码修改而来，用以替代原本只有游戏签到一个功能的简单脚本。
---
<details>
  <summary>【异环·塔吉多】暂留</summary>

```
task yongyeym_AutoSign_QingLong_main/tajiduo_sign.py
```
#### 异环&塔吉多 国服 每日游戏签到
##### 塔吉多异环版区每日签到、异环每日签到、塔吉多社区每日任务（点赞、浏览、分享）
##### 只对异环处理，没有幻塔的游戏签到
1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量：tajiduo_refresh_token。

#### 更新日志：


2026/04/21：
* 初始版本发布，代码由鸣潮签到脚本代码修改而来，尚未解决ios版用于刷新refreshToken授权码的API所需的ds动态验证加密参数，登录授权码每天会更新，无法连续使用，目前脚本无法运作！
* 如有此游戏签到需求，可看一下Candy-QAQ/NTE-Auto-Sign的项目实现
</details>

---
#### 二重螺旋&皎皎角社区 国服 每日任务与签到
#### 已放弃，不再更新
<details>
  <summary>【点击这里查看详细内容】</summary>

```
task yongyeym_AutoSign_QingLong_main/old_files/dnabbs_sign.py
```
##### 皎皎角社区每日签到、二重螺旋每日签到、皎皎角社区每日任务（点赞、浏览、分享）
##### 关于回复帖子5次的每日任务：经测试，此任务必须回复5个不同的帖子才会计数，且每个帖子都只有一次计数机会，即非同一天回复同一个帖子时，此任务也不会计数。由于以上限制，无法直接对官方水贴回复5次来完成任务，随机水贴回复其他玩家帖子可能出现不可预料的情况，因此放弃自动处理此任务。
1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量：dnabbs，可从[皎皎角PC端网页](https://dnabbs.yingxiong.com/pc)获取账号cookie（ey开头）；

#### 更新日志：

2026/03/03:
* 游戏退坑，不再更新此脚本，脚本移动到/old_files/dnabbs_sign.py
* （因本人对加密和爬虫逆向方面完全不懂，现学现卖，请求堆栈里看了半天也没找到Tn值在哪里生成的，如有哪位大佬找到了求解惑）
* 因移动端增加了代理检测，常规手段无法抓包，但脚本中的请求参数理论上只需要补上签名验证key就可以正常使用，有需要的可自行尝试。

2026/02/04：
* 目前更多请求增加了签名验证key，如游戏签到和点赞操作，实际上两周前官方就已经更新了此验证，但恰逢终末地公测，沉迷爆肝拉电线去了……
* 同时期IOS版APP也增加了代理检测，挂任何代理APP都会直接禁止自身网络访问，使得抓包API异常麻烦，实力不足，只能暂时用原有抓包的数据用着……
* 由于签名验证key机制无法使用随机值过验证，且key值会根据请求每次单独生成，抓包获取的key可用时间仅有一两天，因此删除了之前增加的两个验证key变量，环境变量中不再需要配置。
* 暂无法获取签名验证key的生成规则，调整了社区任务部分的执行顺序，将不需要使用签名验证key的操作任务放到最前方执行，确保基本可用。

2025/12/12：
* 初始版本发布

</details>

---
