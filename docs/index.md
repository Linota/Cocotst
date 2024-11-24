
**本项目仅支持 Webhook 事件推送**

**请自行反向代理 Webhook 服务器并添加 HTTPS**

**推送地址为 `https://your.domain/postevent`**

**请注意, 本项目未对 Webhook 所接收的数据进行校验，后期将会添加签名校验**

Cocotst 依赖于 [`GraiaProject`](https://github.com/GraiaProject)
相信它可以给你带来良好的 `Python QQ Bot` 开发体验.



## 安装

`pdm add cocotst`

或

`poetry add cocotst`

或

`pip install cocotst`

> 我们强烈建议使用 [`pdm`](https://pdm.fming.dev) / [`poetry`](https://python-poetry.org) 进行包管理

## ✨Features

### Supports

- ✅ C2C 消息接收发送
- ✅ 群 消息接收发送
- ✅ 媒体消息发送

### TODO

以下特性有可能逐渐被添加

- ⭕ Alconna
- ⭕ 机器人加入群聊事件
- ⭕ C2C 添加机器人事件
- ⭕ 群聊移除机器人事件
- ⭕ C2C 移除机器人事件
- ⭕ 群聊允许机器人发送主动消息事件
- ⭕ 群聊禁止机器人发送主动消息事件
- ⭕ C2C 允许机器人发送主动消息事件
- ⭕ C2C 禁止机器人发送主动消息事件
- ⭕ 频道支持
- ⭕ Markdown 消息支持
- ⭕ 消息撤回
- ⭕ Keyboard 消息支持
- ⭕ ~~ARK, Embed 消息支持~~


## 开始使用

```python
from cocotst.event.message import GroupMessage
from cocotst.network.model import Target
from cocotst.app import Cocotst
from cocotst.network.model import WebHookConfig
from cocotst.message.parser.base import QCommandMatcher

app = Cocotst(
    appid="",
    clientSecret="",
    webhook_config=WebHookConfig(host="0.0.0.0", port=2099),
    is_sand_box=True,
)

@app.broadcast.receiver(GroupMessage, decorators=[QCommandMatcher("ping")])
async def catch(app: Cocotst, target: Target):
    await app.send_group_message(target, content="pong!")

if __name__ == "__main__":
    app.launch_blocking()
```



## 讨论

Graia QQ 交流群: [邀请链接](https://jq.qq.com/?_wv=1027&k=VXp6plBD)

> QQ 群不定时清除不活跃成员, 请自行重新申请入群.





**如果认为本项目有帮助, 欢迎点一个 `Star`.**

