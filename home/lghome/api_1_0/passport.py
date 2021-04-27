from . import api
from flask import request, jsonify, session
from lghome.response_code import RET
from lghome import redis_store
from lghome.models import User
from lghome import db
from lghome import constants
import re
import logging


@api.route("/users", methods=["POST"])
def register():
    """
    注册
    :param: 手机号 短信验证码  密码 确认密码
    :return: json
    """
    # 接收参数
    request_dict = request.get_json()
    mobile = request_dict.get("mobile")
    sms_code = request_dict.get("sms_code")
    password = request_dict.get("password")
    password2 = request_dict.get("password2")

    # 验证
    if not all([mobile, sms_code, password, password2]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 判断手机号格式
    if not re.match(r'1[345678]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')

    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg='两次密码不一致')

    # 从redis取短信验证码
    try:
        real_sms_code = redis_store.get("sms_code_%s" % mobile)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='读取短信验证码异常')
    # 判断短信验证码是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg='短信验证码失效')

    # 删除redis中的短信验证码。当你输入错误短信验证码，进行点击'注册'后，是显示错误的。后面你去填写正确短信验证码后，
    # 再点击'注册'还是错误，因为已经失效了。步骤就在这里。
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        logging.error(e)
    # 判断用户填写的验证码的正确性
    real_sms_code = real_sms_code.decode()
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码错误')
    # # 判断手机号是否存在
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     logging.error(e)
    # else:
    #     if user is not None:
    #         # 表示手机号已经被注册过
    #         return jsonify(errno=RET.DATAEXIST, errmsg='手机号已经存在')
    # 保存数据

    # 保存用户信息和密码加密
    user = User(name=mobile, mobile=mobile)
    # 这个语句就触发了User类里面@property和 @password.setter从而成立
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()
    # 因为User类这个模型里面mobile是唯一字段。所以如果已经存在一个手机号，还去插入这个手机号，就会报IntegrityError这个错误
    except IntegrityError as e:
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg='手机号已经存在')
    except Exception as e:
        # 回滚
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='插入数据库异常')

    # 保存登录状态到session中
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    # 返回结果
    return jsonify(errno=RET.OK, errmsg='注册成功')


@api.route("/sessions", methods=["POST"])
def login():
    """
    用户登录
    :param: 手机号,密码
    :return: json
    """
    # 接收参数
    request_dict = request.get_json()
    mobile = request_dict.get('mobile')
    password = request_dict.get('password')
    # 校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 判断手机号格式
    if not re.match(r'1[345678]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    # 业务逻辑处理
    # 判断一下子错误次数是否超过限制,如果超过限制就不给你验证登录了。我直接给你返回。等600s后在解除
    # request.remote_addr获取访问我网站的用户ip
    user_ip = request.remote_addr
    try:
        #就算access_nums_192.168.xxx没有这个key,取出来的是None而不会报错，报错也是连接redis问题
        access_nums = redis_store.get("access_nums_%s" % user_ip)
    except Exception as e:
        logging.error(e)
    else:
        if access_nums is not None and int(access_nums) >= constants.LOGIN_ERROR_MAX_TIMES:
            return jsonify(errno=RET.REQERR, errmsg='错误次数太多,请稍后重试')

    # 从数据库中查询手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
        # 查询时候的异常
        return jsonify(errno=RET.DBERR, errmsg='获取用户信息失败')
    # 验证密码。如果用手机号查询数据库，查询出来的是None或者验证密码得到结果False。如果验证成功是不会执行下面的代码
    if user is None or not user.check_pwd_hash(password):
        try:
            # 密码或手机号错误后，就记录你这个访问我网站的ip访问的数量
            redis_store.incr("access_nums_%s" % user_ip)
            # 600秒后删除记录你这个访问我网站的ip访问的数量
            redis_store.expire("access_nums_%s" % user_ip, constants.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            logging.error(e)

        return jsonify(errno=RET.DATAERR, errmsg='账号密码不匹配')
    # 保存登录状态
    session['name'] = user.name
    session['mobile'] = user.mobile
    session['user_id'] = user.id

    # 返回
    return jsonify(errno=RET.OK, errmsg='登录成功')


# 在跳转首页时，会触发这个视图
@api.route("/session", methods=["GET"])
def check_login():
    """
    检查登录状态
    :return: 用户的信息或者返回错误信息
    """

    name = session.get('name')

    # 首页的js（index.js）里面，接收到这个视图返回的值后，
    if name is not None:
        # 如果errono等于0，则表示登录，然后在首页头部显示个人中心图标，然后使用传过来的name显示信息
        return jsonify(errno=RET.OK, errmsg='true', data={"name": name})
    else:
        # 如果errno是其他则不显示个人中心图标
        return jsonify(errno=RET.SESSIONERR, errmsg='false')


# 点击退出，触发my.js里面delete的请求。
@api.route("/session", methods=["DELETE"])
def logout():
    """退出登录"""
    # 清空session
    session.clear()
    return jsonify(errno=RET.OK, errmsg='OK')


