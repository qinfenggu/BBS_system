from django.contrib.auth.backends import ModelBackend
from .models import User
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
from . import constants
import re


def get_user_by_account(username):
    """
    获取user对象
    :param username: 用户名或手机号
    :return:
    """
    try:
        if re.match(r'^1[3-9]\d{9}', username):
            user = User.objects.get(mobile=username)
        else:
            user = User.objects.get(username=username)
    except:
        return None
    else:
        return user


class UsernameMobileBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写认证方法
        :param username: 用户名或手机号
        :param password: 密码明文
        :param kwargs: 额外参数
        :return: user
        """
        # 判断传过来的是否是手机号

        user = get_user_by_account(username)

        if user and user.check_password(password):
            return user
        else:
            return None


def generate_verify_email_url(user):
    """
    生成邮箱激活链接
    :return: 邮箱激活链接
    http://www.meiduo.site:8000/emails/verification/?token=eyJhbGciOiJIUzUxMiIsImlhdCI6MTYxMjUxMzEwMSwiZXhwIjoxNjEyNTk5NTAxfQ.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6IjI3MDUxODU4MzRAcXEuY29tIn0.bNHVCzCjBw2yO3RKqnI3tICLN97xwvKcqFC-qip2XAEpG2hXuCl2vn3E8Q_WxRF0i_z3scqsWokz8rnOV-pxQw
    """
    # 这个是一种djnago自带加密方式
    s = Serializer(settings.SECRET_KEY, constants.VERIFY_EMAIL_TOKEN_EXPIRES)

    data = {'user_id': user.id, 'email': user.email}

    token = s.dumps(data)

    return settings.EMAIL_VERIFY_URL + '?token=' + token.decode()


def check_verify_email_token(token):
    """
    反序列token 获取user,解密token得出user_id、email反序列token 获取user
    :param token: 序列化之后的用户信息
    :return: user
    """
    s = Serializer(settings.SECRET_KEY, constants.VERIFY_EMAIL_TOKEN_EXPIRES)

    try:
        data = s.loads(token)
    except:
        return None
    else:
        user_id = data.get('user_id')
        email = data.get('email')
        try:
            user = User.objects.get(id=user_id, email=email)
        except User.DoesNotExist:
            return None
        else:
            return user