# @ Time    : 2020/11/20 20:44
# @ Author  : JuRan

from . import api
from lghome.utils.captcha.captcha import captcha
from lghome import redis_store
import logging
from flask import jsonify, make_response, request
from lghome import constants
from lghome.response_code import RET
from lghome.models import User
import random
from lghome.libs.ronglianyun.ccp_sms import CCP
from lghome.tasks.sms.tasks import send_sms


# 每次请求注册页面时，都会请求 127.0.0.1/api/v1.0/image_codes/<image_code_id>下面这个视图。具体怎么请求前端的事
# 而且每次前端那边都会利用uuid生成唯一的image_code_id。从而区别所生成的验证码到底是哪次请求
@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """
    获取图片验证码
    :param image_code_id: 图片的编号
    :return: 验证码,验证码图像
    """
    # 验证参数
    # 业务逻辑处理
    # 生成验证码图片。captcha.generate_captcha()会生成验证码和图形验证码的一张图片
    text, image_data = captcha.generate_captcha()
    # 保存验证码
    # redis_store.set()
    # redis_store.exprie()
    try:
        redis_store.setex('image_code_%s' % image_code_id, constants.IAMGE_CODE_REDIS_EXPIRES, text)
        print('图形验证码:%s' % text)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存图片验证码失败')

    # 返回值
    response = make_response(image_data)
    response.headers['Content-Type'] = 'image/jpg'
    return response


# 这里设置url可以使用正则表达式re原因都依靠前面重写 BaseConverter方法功劳
@api.route("/sms_codes/<re(r'1[345678]\d{9}'):mobile>")
def get_sms_code(mobile):
    """获取短信验证码"""

    # 图片验证码
    image_code = request.args.get('image_code')
    # 获取UUID
    image_code_id = request.args.get('image_code_id')

    # 校验参数图形验证码和UUID是否存在
    if not all([image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    try:
        # 从redis中取出验证码
        real_image_code = redis_store.get('image_code_%s' % image_code_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='redis数据库异常')

    # 判断图片验证码是否过期。不管你有没有'image_code_手机号'都可以被取，不会报错。如果没有'image_code_手机号'取出来的是None
    if real_image_code is None:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码失效')

    try:
        # 删除redis中的图片验证码。这就是为什么，以前你输入验证码错误，去点击发送短信验证码发送不了提示图形验证码错误，
        # 然后你输入正确的图形验证码后再点击发送短信验证码，还是不行，因为那个图形验证码已经没用了。在这里被删除掉了
        redis_store.delete('image_code_%s' % image_code_id)
    except Exception as e:
        logging.error(e)

    # 与用户填写的图片验证码对比。decode()作用：因为从redis里面取出来的数据是字节，需要decode()转换后成字符
    real_image_code = real_image_code.decode()
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')

    try:
        # 判断手机号的操作。判断记录已经发送短信验证码的记录是否存在
        send_flag = redis_store.get('send_sms_code_%s' % mobile)
    except Exception as e:
        logging.error(e)
    else:
        if send_flag is not None:
            return jsonify(errno=RET.REQERR, errmsg='请求过于频繁')

    # 判断手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
    else:
        if user is not None:
            # 表示手机号已经被注册过
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已经存在')

    # 生成短信验证码
    sms_code = "%06d" % random.randint(0, 999999)

    try:
        # redis管道。保存真实的短信验证码到redis
        pl = redis_store.pipeline()
        pl.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送给这个手机号的记录。保存时间为60秒。用户上面验证是否通过postman软件没60s就恶意又发送
        pl.setex('send_sms_code_%s' % mobile, constants.SNED_SMS_CODE_EXPIRES, 1)
        pl.execute()

    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存短信验证码异常')

    # # 发短信。不用异步
    # try:
    #     ccp = CCP()
    #     # datas：(短信验证码， 过期时间数字n分钟)。所以才要/60
    #     result = ccp.send_message(mobile, (sms_code, int(constants.SMS_CODE_REDIS_EXPIRES/60)), 1)
    # except Exception as e:
    #     logging.error(e)
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送异常')
    #
    # # 返回值
    # if result == 0:
    #     return jsonify(errno=RET.OK, errmsg='发送成功')
    # else:
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送失败')

    # 发送短信。用异步
    send_sms.delay(mobile, (sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)), 1)
    return jsonify(errno=RET.OK, errmsg='发送成功')

