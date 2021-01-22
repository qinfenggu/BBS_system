from flask import g, redirect, url_for
from functools import wraps


#  这个装饰器作用：判断当前用户是否拥有need_required_permission权限。如果没有则重定向到首页
def permission_required(need_required_permission):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            user = g.user
            # 判断当前用户是否有这个需要请求的权限。user.has_permissions返回是布尔值
            if user.has_permissions(need_required_permission):
                return func(*args, **kwargs)
            else:
                return redirect(url_for('cms.home_page'))
        return inner
    return wrapper

