# @ Time    : 2020/5/13 21:00
# @ Author  : JuRan

from flask import jsonify


class HttpCode(object):
    ok = 200
    unautherror = 401
    paramerror = 400
    servererror = 500


def restful_result(code, message, data):
    return jsonify({"code": code, "message": message, "data": data})


def success(message="", data=None):
    return restful_result(code=HttpCode.ok, message=message, data=data)


def unauth_error(message=""):
    return restful_result(code=HttpCode.unautherror, message=message, data=None)


def params_errors(message=""):
    return restful_result(code=HttpCode.paramerror, message=message, data=None)


def server_errors(message="服务器内部错误"):
    return restful_result(code=HttpCode.servererror, message=message, data=None)


