"""重写BaseConverter，主要是为了可以在定义路由时可以自定义正则表达式"""
from werkzeug.routing import BaseConverter
from flask import session, jsonify, g
from lghome.response_code import RET
import functools


class ReConverter(BaseConverter):
    def __init__(self, map, regex):
        super().__init__(map)
        # super(ReConverter, self).__init__(map)
        self.regex = regex


# view_func 被装饰的函数
def login_required(view_func):
    # 不修改原有函数的属性
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        # 判断用户的登录状态。
        user_id = session.get('user_id')
        if user_id is not None:
            # 已登录
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            # 未登陆
            return jsonify(errno=RET.SESSIONERR, errmsg='用户未登陆')

    return wrapper
