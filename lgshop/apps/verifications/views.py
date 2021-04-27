from django.shortcuts import render
from django.views import View
from verifications.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse

from verifications.libs.captcha.captcha import captcha
from verifications.libs.ronglianyun.ccp_sms import CCP
from verifications import constants
from utils.response_code import RETCODE

from celery_tasks.sms.tasks import send_sms_code
import logging
import random

logger = logging.getLogger('django')


# 图形验证码
class ImageCodeView(View):
    """图形验证码"""
    # uuid作用:可以识别
    def get(self, request, uuid):
        """
        :param uuid: 通用唯一识别符,用于标识唯一图片验证码属于哪个用户的
        :return: image/jpg
        """

        # 生成图片验证码
        text, image = captcha.generate_captcha()
        print('验证码:', text)

        # 连接redis，选择使用verify_code这个库
        redis_conn = get_redis_connection('verify_code')

        # 数据保存到数据库里面
        redis_conn.setex('img_%s' % uuid, 300, text)
        # 响应图形验证码
        return HttpResponse(image, content_type='image/png')


# 短信验证码
class SMSCodeView(View):

    def get(self, request, mobile):
        """
        :param mobile: 手机号
        :return: JSON
        """

        # 查询访问这个视图url后面？参数值。输入的图形验证码image_code_client数据和uuid
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        print('uuid:', uuid)

        # 校验。image_code_client, uuid都没有值就是在前端没有传
        if not all([image_code_client, uuid]):
            return HttpResponseForbidden('缺少必传参数')

        # 连接对应的redis数据库
        redis_conn = get_redis_connection('verify_code')
        # 取验证码。
        send_flag = redis_conn.get("send_flag_%s" % mobile)
        if send_flag:
            return JsonResponse({"code": 111, "errmsg": "短信发送过于频繁"})

        image_code_server = redis_conn.get('img_%s' % uuid)
        print('image_code_server:', image_code_server)

        # redis里面取不出验证码。
        if image_code_server is None:
            return JsonResponse({"code": RETCODE.IMAGECODEERR, 'errmsg': '图像验证码已失效了'})

        # 删除图形验证码
        redis_conn.delete('img_%s' % uuid)
        # 验证前端传过的图形验证是否和从redis里面取出来的验证码一致.image_code_server.decode()原因是image_code_server是字节
        if image_code_client.lower() != image_code_server.decode().lower():
            return JsonResponse({"code": RETCODE.IMAGECODEERR, 'errmsg': "图形验证码输入有误"})

        # 生成短信验证码：生成6位数验证码，不足0补全
        sms_code = "%06d" % random.randint(0, 999999)

        # 保存到日志中
        logger.info(sms_code)
        # sms_code
        # for i in range(6):
        #     sms_code += str(random.randint(0, 9))

        # 保存短信验证码
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)

        # 保存短信验证码是否已经发送
        # redis_conn.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_FLAG, 1)

        # 通过redis管道来实现
        # 创建redis管道
        pl = redis_conn.pipeline()
        # 将命令添加到队列
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_FLAG, 1)
        # 执行
        pl.execute()

        # 发送短信验证码
        # CCP().send_message(mobile, (sms_code, constants.SMS_CODE_REDIS_EXPIRES//60), 1)
        # 错误的写法
        # send_sms_code(mobile, sms_code)
        send_sms_code.delay(mobile, sms_code)
        print('短信验证码发送成功')

        # 响应结果
        return JsonResponse({"code": RETCODE.OK, 'errmsg': "发送短信验证码成功"})