from yunpian_python_sdk.model import constant as YC
from yunpian_python_sdk.ypclient import YunpianClient


# 云片网发送短信api接口
def send_mobile_note(mobile, code):
    # 连接云片网
    # clnt = YunpianClient('0963f9d693d4e0a797c04da3991da876')
    clnt = YunpianClient('e8abe129a4e9f9a7c8c9adc8ece9ebc9')
    param = {YC.MOBILE: mobile, YC.TEXT: '【于成令】您的验证码是{}'.format(code)}
    # 发送短信验证码
    r = clnt.sms().single_send(param)
    return r.code()


# r.code()  状态码。0表示发送成功
# r.msg()   只显示两种信息：发送成功，发送失败
# r.data()  是一个字典，里面有状态码，msg，手机号，RMB这些信息
