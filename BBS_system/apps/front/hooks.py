# @ Time    : 2020/5/11 20:54
# @ Author  : JuRan

from flask import request, url_for, redirect, session, g
from .views import front_bp
from .models import FrontUser


# 通过钩子函数
@front_bp.before_request
def before_request():
    if 'front_user_id' in session:
        user_id = session.get('front_user_id')
        user = FrontUser.query.get(user_id)
        # print(CMSUser.query.filter(CMSUser.email == 'admin@qq.com').first())
        if user:
            g.front_user = user


