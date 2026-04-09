# WeChat-auto-listener-reply

微信自动监听与回复（支持关键词命中后 Bark 提醒 + 自动回复）。

## 功能

- 持续监听全部新消息（群聊与个人聊天）。
- 命中关键词后：
  - 发送 Bark 推送通知。
  - 自动给对应会话回复固定文案。

## 使用步骤

1. 安装依赖（示例）：

```bash
pip install wxauto4
```

2. 编辑 `main.py` 顶部配置：

- `KEYWORDS`: 关键词列表。
- `BARK_BASE_URL`: Bark 推送地址（例如 `https://api.day.app/<你的key>`）。
- `AUTO_REPLY_TEXT`: 自动回复内容。
- `POLL_INTERVAL`: 监听轮询间隔（秒）。

3. 运行：

```bash
python main.py
```

## 说明

- 脚本会尽量兼容 `wxauto4` 不同版本的字段/方法命名。
- 若 Bark 地址为空，则仅做本地打印与自动回复，不发送推送。
- 自动回复发送失败时会打印错误，但不会中断监听。
