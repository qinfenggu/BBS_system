# @ Time    : 2020/7/27 21:40
# @ Author  : JuRan

from ronglian_sms_sdk import SmsSDK
import json

accId = '8a216da85741a1b901574fb0b1210982'
accToken = '15fb1a43ed5c4ddb83531b7e544448c5'
appId = '8a216da85741a1b901574fb0b17d0987'


class CCP(object):

    def __new__(cls, *args, **kwargs):
        # print(super().__new__(cls, *args, **kwargs))
        # cls._instance => CCP
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.sdk = SmsSDK(accId, accToken, appId)
        return cls._instance

    def send_message(self, mobile, datas, tid):
        resp = self._instance.sdk.sendMessage(tid, mobile, datas)
        result = json.loads(resp)
        if result['statusCode'] == '000000':
            return 0
        else:
            return -1
