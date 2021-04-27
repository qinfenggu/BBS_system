# @ Time    : 2020/7/27 21:40
# @ Author  : JuRan

from ronglian_sms_sdk import SmsSDK
import json

accId = '8a216da85741a1b901574fb0b1210982'
accToken = '15fb1a43ed5c4ddb83531b7e544448c5'
appId = '8a216da85741a1b901574fb0b17d0987'


class CCP(object):
    """
    发送短信：容联云平台
    """

    def __new__(cls, *args, **kwargs):
        # print(super().__new__(cls, *args, **kwargs))
        # cls._instance => CCP
        # 如果是第一次实例化，应该返回实例化后的对象，如果是第二次实例化，应该返回上一次实例化后的对象
        if not hasattr(cls, '_instance'):
            # 重写继承new方法
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.sdk = SmsSDK(accId, accToken, appId)
        return cls._instance

    def send_message(self, mobile, datas, tid):
        # tid 表示选择哪个模板。datas表示验证码和过期时间
        resp = self._instance.sdk.sendMessage(tid, mobile, datas)
        result = json.loads(resp)
        # 状态码是00000表示发送成功
        if result['statusCode'] == '000000':
            return 0
        else:
            return -1
