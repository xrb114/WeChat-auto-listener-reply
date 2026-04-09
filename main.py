import json
import time
from typing import Iterable

from wxauto4 import WeChat

# ====== 配置区 ======
# 命中关键词后会自动跳转到对应会话回复，然后回到主页继续监听
KEYWORDS = ["关键词1", "告警", "紧急"]
# 自动回复内容
AUTO_REPLY_TEXT = "已收到你的消息，我会尽快处理。"
# 轮询间隔秒数
POLL_INTERVAL = 1.0
# 主页模式下，如果库支持相关 API，会主动回到主页再继续监听
ALWAYS_BACK_HOME = True
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
    for name in ("chat_name", "session_name", "sender", "from_user", "who"):
        value = getattr(msg, name, None)
        if value:
            return str(value)
    return ""


def has_keyword(text: str, keywords: Iterable[str]) -> str | None:
    for kw in keywords:
        if kw and kw in text:
            return kw
    return None


def call_first_available(obj, method_names, *args, **kwargs):
    """按顺序调用第一个存在的方法，找不到返回 False。"""
    for name in method_names:
        method = getattr(obj, name, None)
        if callable(method):
            method(*args, **kwargs)
            return True
    return False


def go_home(wx: WeChat) -> bool:
    """尝试回到微信主页（不同版本 API 名称可能不同）。"""
    return call_first_available(
        wx,
        [
            "BackToHome",
            "GoToHome",
            "GoHome",
            "GotoHome",
            "MainPage",
            "SwitchToHome",
        ],
    )


def jump_to_chat(wx: WeChat, chat_name: str) -> bool:
    """从主页跳转到目标会话。"""
    if not chat_name:
        return False
    return call_first_available(wx, ["ChatWith", "SwitchToChat", "OpenChat", "OpenSession"], chat_name)


def send_reply(wx: WeChat, text: str) -> bool:
    """发送自动回复。"""
    if hasattr(wx, "SendMsg"):
        wx.SendMsg(text)
        return True
    if hasattr(wx, "SendText"):
        wx.SendText(text)
        return True
    return False


def main() -> None:
    wx = WeChat()
    seen_ids = set()

    if ALWAYS_BACK_HOME:
        go_home(wx)

    while True:
        try:
            if ALWAYS_BACK_HOME:
                go_home(wx)

            msgs = wx.GetAllMessage()
            for msg in msgs:
                msg_id = getattr(msg, "id", None) or getattr(msg, "msgid", None) or hash(str(msg))
                if msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)

                text = safe_text(msg)
                keyword = has_keyword(text, KEYWORDS)
                if not keyword:
                    continue

                chat_name = safe_chat_name(msg)
                print(f"命中关键词[{keyword}]，会话[{chat_name}]，开始处理。")

                jumped = jump_to_chat(wx, chat_name)
                if not jumped:
                    print(f"无法跳转到会话: {chat_name}")
                    continue

                replied = send_reply(wx, AUTO_REPLY_TEXT)
                if not replied:
                    print("未找到可用发送方法（SendMsg/SendText）。")

                if ALWAYS_BACK_HOME:
                    go_home(wx)

            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("手动停止监听。")
            break
        except Exception as loop_err:
            print(f"监听循环异常: {loop_err}")
            if ALWAYS_BACK_HOME:
                go_home(wx)
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
