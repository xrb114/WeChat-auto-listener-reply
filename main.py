import json
import time
import urllib.parse
import urllib.request
from typing import Iterable

from wxauto4 import WeChat

# ====== 配置区 ======
# 关键词命中后会触发 Bark 通知 + 自动回复
KEYWORDS = ["关键词1", "告警", "紧急"]
# Bark 推送地址（示例："https://api.day.app/你的key"）
BARK_BASE_URL = ""
# 自动回复内容
AUTO_REPLY_TEXT = "已收到你的消息，我会尽快处理。"
# 轮询间隔秒数
POLL_INTERVAL = 1.0
# ====================


def safe_text(msg) -> str:
    """尽可能兼容不同消息结构，提取可匹配文本。"""
    parts = []
    for name in ("content", "text", "raw"):
        value = getattr(msg, name, None)
        if value:
            parts.append(str(value))
    if not parts:
        try:
            return json.dumps(getattr(msg, "__dict__", {}), ensure_ascii=False)
        except Exception:
            return str(msg)
    return " | ".join(parts)


def safe_chat_name(msg) -> str:
    for name in ("chat_name", "sender", "from_user", "who"):
        value = getattr(msg, name, None)
        if value:
            return str(value)
    return "未知会话"


def is_group_chat(msg) -> bool:
    """根据常见字段推断是否群聊，无法判断时返回 False（按个人聊天处理）。"""
    raw = str(getattr(msg, "raw", ""))
    text = safe_text(msg)
    markers = [
        str(getattr(msg, "is_group", "")).lower(),
        str(getattr(msg, "chat_type", "")).lower(),
        raw.lower(),
        text.lower(),
    ]
    return any("group" in m or "群" in m for m in markers)


def has_keyword(text: str, keywords: Iterable[str]) -> str | None:
    for kw in keywords:
        if kw and kw in text:
            return kw
    return None


def send_bark(base_url: str, title: str, body: str) -> None:
    if not base_url:
        return
    url = f"{base_url.rstrip('/')}/{urllib.parse.quote(title)}/{urllib.parse.quote(body)}"
    with urllib.request.urlopen(url, timeout=5) as resp:
        resp.read()


def auto_reply(wx: WeChat, chat_name: str, text: str) -> None:
    # 兼容不同 API 命名
    if hasattr(wx, "ChatWith"):
        wx.ChatWith(chat_name)
    if hasattr(wx, "SendMsg"):
        wx.SendMsg(text)
    elif hasattr(wx, "SendText"):
        wx.SendText(text)


def main() -> None:
    wx = WeChat()
    seen_ids = set()

    while True:
        try:
            msgs = wx.GetAllMessage()
            for msg in msgs:
                msg_id = getattr(msg, "id", None) or getattr(msg, "msgid", None) or hash(str(msg))
                if msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)

                text = safe_text(msg)
                chat_name = safe_chat_name(msg)
                keyword = has_keyword(text, KEYWORDS)
                if not keyword:
                    continue

                chat_type = "群聊" if is_group_chat(msg) else "个人"
                title = f"微信{chat_type}关键词提醒"
                body = f"会话: {chat_name} | 命中: {keyword} | 内容: {text[:120]}"
                print(body)

                try:
                    send_bark(BARK_BASE_URL, title, body)
                except Exception as bark_err:
                    print(f"Bark 推送失败: {bark_err}")

                try:
                    auto_reply(wx, chat_name, AUTO_REPLY_TEXT)
                except Exception as reply_err:
                    print(f"自动回复失败: {reply_err}")

            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("手动停止监听。")
            break
        except Exception as loop_err:
            print(f"监听循环异常: {loop_err}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
