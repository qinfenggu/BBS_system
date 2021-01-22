from flask import Blueprint, request
from utils import yunpian_send_note_api, restful
from utils.random_captcha import get_random_note_captcha
from utils import redis_save_capthcha
from .forms import SMSCaptchaForm

common_bp = Blueprint('common', __name__, url_prefix='/c/')


# @common_bp.route('/sms_captcha/', methods=['POST'])
# def send_note_captcha():
#     telephone = request.form.get('telephone')
#     # 如果手机号不存在
#     if not telephone:
#         return restful.params_errors(message='请填写手机号')
#     captcha = get_random_captcha(6)
#     if yunpian_send_note_api.send_mobile_note(telephone, captcha) == 0:
#         return restful.success()
#     else:
#         return restful.params_errors(message='发送失败')

# 发送短信验证码
@common_bp.route("/sms_captcha/", methods=['POST'])
def sms_captcha():
    telephone = request.form.get('telephone')
    # 如果手机号不存在
    if not telephone:
        return restful.params_errors(message='请填写手机号')
    form = SMSCaptchaForm(request.form)
    if form.validate():
        captcha = get_random_note_captcha(6)
        if yunpian_send_note_api.send_mobile_note(telephone, captcha) == 0:
            # 把短信验证码保存到redis
            redis_save_capthcha.redis_set(telephone, captcha)
            return restful.success()
        else:
            return restful.params_errors(message='发送失败')

    else:
        return restful.params_errors(message='参数错误')

