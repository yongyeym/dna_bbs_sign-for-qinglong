# 自用青龙面板自动脚本 AutoSign_QingLong
### 自己NAS的青龙面板自用脚本，有需要的可自取使用及改造
1. 青龙面板添加依赖：Python3的Requests包；
2. 使用青龙面板自带的推送服务，需要在青龙配置文件中添加自己需要推送的APP的Key，若不需要推送则不填；
3. 订阅本仓库，添加定时任务。

```
task yongyeym_AutoSign_QingLong_main/dnabbs-sign.py
```
#### 二重螺旋&皎皎角社区 国服 每日任务与签到
##### 皎皎角社区每日签到、二重螺旋每日签到、皎皎角社区每日任务（点赞、浏览、分享）
##### 回复帖子5次的每日任务：经测试，此任务必须回复5个不同的帖子才会计数，且疑似每个帖子都只有一次计数机会，即非同一天回复同一个帖子时，此任务也不会计数。由于以上限制，无法直接对官方水贴回复5次来完成任务，随机水贴回复其他玩家帖子可能出现不可预料的情况，因此放弃自动处理此任务。

1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量：dnabbs，可从[皎皎角社区PC网址](https://dnabbs.yingxiong.com/pc)获取账号cookie（ey开头）；

```
task yongyeym_AutoSign_QingLong_main/kurobbs-sign.py
```
#### 鸣潮&库街区 国服 每日游戏签到
##### 目前仅游戏签到，URL请求参数来自鸣潮Tool工具作者的实现，暂时这么用着，有需要的可以拿去用
##### 后续可能会重做这个脚本，并增加类似二重螺旋脚本的社区任务、签到奖励详情等功能

1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量：kurobbs，可从[库街区PC网址](http://www.kurobbs.com/mc/home/9)获取账号cookie（ey开头）；

```
task yongyeym_AutoSign_QingLong_main/nga-sign.py
```
#### NGA社区 每日签到
##### 在做了在做了

1. 默认自动执行时间为每天凌晨3分，cron：0 3 0 * * ?
2. 青龙面板添加环境变量，可从[NGA社区PC网址](https://bbs.nga.cn/)获取cookie中部分内容： 
   * 从F12的网络选项卡中，找到nuke.php、bbs.nga.cn等请求，请求header中找到cookie。
   * nga_uid：账号的UID，可直接去个人页找到，也可以在PC版cookie中的ngaPassportUid，移动版cookie中的access_uid中看到；
   * nga_cookie：账号的Cookie，在PC版cookie中的ngaPassportCid，移动版cookie中的access_token中看到；
   * nga_user_info：个人资料，来自cookie中的ngacn0comUserInfo，可能需要，每个人不同包含个人昵称，在测试中……
   * 等等更多……