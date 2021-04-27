# 定义任务
from celery_tasks.sms.ronglianyun.ccp_sms import CCP
from . import constants
from celery_tasks.main import celery_app


# 保证celery识别任务, name是任务的名字
@celery_app.task(name="send_sms_code")
def send_sms_code(mobile, sms_code):
    """
    发送短信验证码的异步任务
    :param mobile: 手机号
    :param sms_code: 短信验证码
    :return: 成功 0 失败 -1
    """
    # constants.SMS_CODE_REDIS_EXPIRES // 60 除以60原因:容联云平台过期时间是按分钟的
    result = CCP().send_message(mobile, (sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60), 1)
    return result
