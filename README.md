# 青龙面板自动脚本 AutoSign_QingLong
### 个人NAS的青龙面板自用脚本
##### 因测试有限，可能会有意料之外的Bug，遇到对应问题后会修复。
##### ⚠ 请勿大范围传播，如有需要可自由使用或改造本仓库代码 ⚠
1. 青龙面板添加依赖：Python3的Requests包；
2. 使用青龙面板自带的推送服务，需要在青龙配置文件中添加自己需要推送的APP的Key，若不需要推送则不填；
3. 青龙面板添加需要的环境变量，也可以改为使用脚本目录下Config/config.ini中[COOKIE]分组内的值（需启用此功能）；
4. 订阅本仓库或clone仓库到本地，添加定时任务；
---
可使用下方代码创建青龙订阅：
```
ql repo https://github.com/yongyeym/AutoSign_QingLong.git
```
---
Config/config.ini配置文件说明：

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
cookie1 = value1
... = ...
```
---
```
task yongyeym_AutoSign_QingLong_main/kurobbs_sign.py
```
#### 鸣潮&库街区 国服 每日游戏签到
##### 库街区每日签到、鸣潮每日签到、库街区社区每日任务（点赞、浏览、分享）
##### 只对鸣潮处理，没有战双帕弥什的游戏签到，但理论上只需要把各参数里的gameId从3改成2即可
##### 目前必须手动设置库街区账号的UID，获取账号信息的API全部需要传入此UID进行查询，但尚未找到可以仅通过token获取此UID的API
##### ⚠ 目前可能存在问题，cookie中用于反爬的acw_tc验证值尚未找到正确的生成方式，目前采用随机生成，可能出现获取到角色UID后，下一个请求返回登录已过期的问题，可从IOS或安卓版库街区APP抓包一个新的账号token再尝试一下 ⚠
1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量：kurobbs，可从[库街区PC端网页](http://www.kurobbs.com/mc/home/9)获取账号token（ey开头）；
3. 青龙面板添加环境变量：kuro_uid，库街区账号的UID，可在库街区个人页找到；
4. 因目前重做的脚本有稳定性问题，保留了老版本仅支持鸣潮游戏签到的脚本/OutdatedScript/kurobbs_only_mingchao_sign.py，如需使用此脚本需要额外手动修改脚本内的roleID，改为自己游戏UID。
---
```
task yongyeym_AutoSign_QingLong_main/dnabbs_sign.py
```
#### 二重螺旋&皎皎角社区 国服 每日任务与签到
##### 皎皎角社区每日签到、二重螺旋每日签到、皎皎角社区每日任务（点赞、浏览、分享）
##### 和库街区APP几乎一模一样的构成，ctrl+c/v后仅需少量修改就可以直接用了，真方便~
##### 关于回复帖子5次的每日任务：经测试，此任务必须回复5个不同的帖子才会计数，且每个帖子都只有一次计数机会，即非同一天回复同一个帖子时，此任务也不会计数。由于以上限制，无法直接对官方水贴回复5次来完成任务，随机水贴回复其他玩家帖子可能出现不可预料的情况，因此放弃自动处理此任务。
1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量：dnabbs，可从[皎皎角PC端网页](https://dnabbs.yingxiong.com/pc)获取账号cookie（ey开头）；
---
```
task yongyeym_AutoSign_QingLong_main/nga_sign.py
```
#### NGA社区 每日签到
##### 仅适配IOS端，需要抓包IOS版APP
##### ⚠ 目前NGA客户端验证参数ngaClientChecksum无法找到正确的生成方式，采用随机生成无法通过验证，使用抓包获得的值也可能失效 ⚠
1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量：nga_uid、nga_cookie、nga_client_checksum
3. 从[NGA社区PC端网页](https://bbs.nga.cn/)或APP抓包获取cookie中部分内容，从F12网络选项卡中，找到nuke.php请求header中的cookie：
   * nga_uid：账号的UID，可以直接去个人主页找到，也可以在PC版cookie中的ngaPassportUid，移动版cookie中的access_uid中找到；
   * nga_cookie：账号的Cookie，在PC版cookie中的ngaPassportCid，移动版cookie中的access_token中看到；
4. 使用IOS抓包工具，抓取IOS版恩基爱论坛APP，从请求头表单中找到__ngaClientChecksum的值：
   * nga_client_checksum：NGA的IOS版客户端校验码，IOS版本是以/uid结尾的字符串，目前只有移动版中存在此参数，尚不清楚如何生成的值，只能抓包获取用着；
---
