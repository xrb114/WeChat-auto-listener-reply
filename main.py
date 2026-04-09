from wxauto4 import WeChat

wx = WeChat()
while True:
    msgs = wx.GetAllMessage()
    for msg in msgs:
        print(msg.raw)