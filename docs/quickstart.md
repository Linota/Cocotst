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