# 快速开始

## 开放平台 Webhook 设置
QQ机器人开放平台支持通过使用HTTP接口接收事件。开发者可通过[管理端](https://q.qq.com/qqbot/#/developer/webhook-setting)设定回调地址，监听事件等。

目前回调地址允许配置的端口号为： 80、443、8080、8443。只能使用 HTTPS 协议。建议使用反向代理工具如 Nginx、Caddy 等进行 HTTPS 转发。

开发者需要提供一个HTTPS回调地址。并选定监听的事件类型。开放平台会将事件通过回调的方式推送给机器人。

<img src='/assets/event_subscription.png'>

本项目默认监听地址为 `https://your.domain/postevent`。后期将加入自定义地址功能。

## 安装 Cocotst

`pdm add cocotst`

或

`poetry add cocotst`

或

`pip install cocotst`

> 我们强烈建议使用 [`pdm`](https://pdm.fming.dev) / [`poetry`](https://python-poetry.org) 进行包管理

## 开始使用

```python
from cocotst.app import Cocotst
from cocotst.event.message import GroupMessage
from cocotst.message.parser.base import QCommandMatcher
from cocotst.network.model import Target, WebHookConfig

app = Cocotst(
    appid="", # 你的 APPID
    clientSecret="", # 你的 ClientSecret
    webhook_config=WebHookConfig(host="127.0.0.1", port=2099), # 你的 Webhook 配置
    is_sand_box=True,
)


@app.broadcast.receiver(GroupMessage, decorators=[QCommandMatcher("ping")])
async def catch(app: Cocotst, target: Target):
    await app.send_group_message(target, content="pong!")


if __name__ == "__main__":
    app.launch_blocking()
```

