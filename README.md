# 自用青龙面板自动脚本 AutoSign_QingLong
### 自己NAS的青龙面板自用脚本
##### ⚠ 请勿大范围传播，如有需要自用的可使用或改造本仓库代码 ⚠
1. 青龙面板添加依赖：Python3的Requests包；
2. 使用青龙面板自带的推送服务，需要在青龙配置文件中添加自己需要推送的APP的Key，若不需要推送则不填；
3. 订阅本仓库，添加定时任务；
4. 因测试条件有限，可能会有意料之外的Bug。
---
可使用下方代码创建青龙订阅：
```
task yongyeym_AutoSign_QingLong_main/kurobbs_sign.py
```
---
```
task yongyeym_AutoSign_QingLong_main/kurobbs_sign.py
```
#### 鸣潮&库街区 国服 每日游戏签到
##### 库街区每日签到、鸣潮每日签到、库街区社区每日任务（点赞、浏览、分享）
##### 只对鸣潮处理，没有战双帕弥什的游戏签到，但理论上只需要把各参数里的gameId从3改成2即可
##### 目前必须手动设置库街区账号的UID，获取账号信息的API全部需要传入此UID进行查询，但尚未找到可以仅通过token获取此UID的API
1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量：kurobbs，可从[库街区PC端网页](http://www.kurobbs.com/mc/home/9)获取账号cookie（ey开头）；
3. 青龙面板添加环境变量：kuro_uid，库街区账号的UID，可在库街区个人页找到；
---
```
task yongyeym_AutoSign_QingLong_main/dnabbs_sign.py
```
#### 二重螺旋&皎皎角社区 国服 每日任务与签到
##### 皎皎角社区每日签到、二重螺旋每日签到、皎皎角社区每日任务（点赞、浏览、分享）
##### 和库街区APP几乎一模一样的构成，ctrl+c/v后仅需少量修改就可以直接用了，真方便~
##### 回复帖子5次的每日任务：经测试，此任务必须回复5个不同的帖子才会计数，且疑似每个帖子都只有一次计数机会，即非同一天回复同一个帖子时，此任务也不会计数。由于以上限制，无法直接对官方水贴回复5次来完成任务，随机水贴回复其他玩家帖子可能出现不可预料的情况，因此放弃自动处理此任务。
1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量：dnabbs，可从[皎皎角PC端网页](https://dnabbs.yingxiong.com/pc)获取账号cookie（ey开头）；
---
```
task yongyeym_AutoSign_QingLong_main/nga_sign.py
```
#### NGA社区 每日签到
##### 仅适配IOS端，需要抓包IOS版APP
1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量：nga_uid、nga_cookie、nga_client_checksum
3. 从[NGA社区PC端网页](https://bbs.nga.cn/)获取cookie中部分内容，从F12网络选项卡中，找到nuke.php请求header中的cookie：
   * nga_uid：账号的UID，可直接去个人页找到，也可以在PC版cookie中的ngaPassportUid，移动版cookie中的access_uid中看到；
   * nga_cookie：账号的Cookie，在PC版cookie中的ngaPassportCid，移动版cookie中的access_token中看到；
4. 使用IOS抓包工具，抓取IOS版恩基爱论坛APP，从请求头表单中找到__ngaClientChecksum的值：
   * nga_client_checksum：NGA的IOS版客户端校验码，是以/uid结尾的字符串，目前只有移动版中存在此参数，尚不清楚如何生成的值，只能抓包获取用着；
---
