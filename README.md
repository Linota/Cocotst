<div align="center">

# Cocotst

_Easily to code qqoffcial bot. ._

🥥

[![PyPI](https://img.shields.io/pypi/v/cocotst)](https://pypi.org/project/cocotst)
[![Python Version](https://img.shields.io/pypi/pyversions/cocotst)](https://pypi.org/project/cocotst)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![License](https://img.shields.io/github/license/Linota/Cocotst)](https://github.com/Linota/Cocotst/blob/master/LICENSE)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)

[![docs](https://img.shields.io/badge/LINOTA-here-blue)](https://ctst.docs.linota.cn/)

[![docs](https://img.shields.io/badge/API_文档-here-purple)](https://ctst.docs.linota.cn/api/NAV/)


</div>

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
- ✅ 机器人加入退出群聊事件
- ✅ 机器人在群中被开关消息推送事件
- ✅ 机器人加入移除 C2C 消息列表事件
- ✅ 机器人在 C2C 中被开关消息推送事件

### TODO

以下特性有可能逐渐被添加

- ⭕ Alconna
- ⭕ 频道支持
- ⭕ Markdown 消息支持
- ⭕ 消息撤回
- ⭕ Keyboard 消息支持
- ⭕ ~~ARK, Embed 消息支持~~

## 结构目录

```
Cocotst
├── docs 文档
├── LICENSE 许可证
├── mkdocs.yml mkdocs 配置文件
├── pdm.lock 依赖锁
├── pyproject.toml 项目配置文件
├── README.md 说明文档
└── src 源码
   └── cocotst 
        ├── all.py 方便引用所有模块
        ├── app.py Tencent API 封装
        ├── config.py 各类配置文件
        ├── dispatcher.py 
        ├── event 事件模块
        │   ├── builtin.py 内置事件
        │   ├── message.py 消息事件
        │   ├── receive.py 开关推送事件
        │   └── robot.py Bot 位置事件
        ├── message 消息模块
        │   ├── element.py 消息元素
        │   ├── parser
        │   │   └── base.py 基础消息解析器
        ├── network 网络模块
        │   ├── model.py 数据模型
        │   ├── services.py 服务模型
        │   ├── sign.py 签名模块
        │   └── webhook.py Webhook 模块，负责接收 Tencent 发送的事件。处理后分发给各个事件处理器
        ├── services.py 服务模块
        └── utils.py 工具模块
```
    

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

## 文档

[![API 文档](https://img.shields.io/badge/API_文档-here-purple)](https://ctst.docs.linota.cn/api/NAV/)
[![官方文档](https://img.shields.io/badge/文档-here-blue)](https://ctst.docs.linota.cn/)



**如果认为本项目有帮助, 欢迎点一个 `Star`.**

