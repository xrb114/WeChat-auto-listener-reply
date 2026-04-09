from wxauto4 import WeChat


wx = WeChat()

# 获取消息
session=wx.GetSession()

print(session)

messages = wx.GetAllMessage()
for msg in messages:
    print(msg.content)
