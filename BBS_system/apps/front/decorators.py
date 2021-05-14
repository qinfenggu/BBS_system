# @ Time    : 2020/5/11 20:51
# @ Author  : JuRan

from flask import session, redirect, url_for
from functools import wraps


# 该装饰器：通过URL访问某个视图之前，先判断session里面是否有front_user_id。没有就重定向回登录页面。主要用在发布帖子。
def front_signin_required(func):
    # @wraps(func)
    def inner(*args, **kwargs):
        if 'front_user_id' in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('front.signin'))
    return inner



