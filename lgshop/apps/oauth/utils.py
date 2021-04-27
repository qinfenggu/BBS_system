# @ Time    : 2021/2/3 21:28
# @ Author  : JuRan
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
from . import constants


def check_access_token(openid):
    """
    反序列化
    :param openid: openid密文
    :return: openid: 明文
    """
    serializer = Serializer(settings.SECRET_KEY, constants.ACCESS_TOKEN_EXPIRES)

    try:
        data = serializer.loads(openid)
    except Exception as e:
        return None
    else:
        return data.get('openid')


def generate_access_token(openid):
    """
    签名、序列化openid
    :param openid: 明文
    :return: openid密文
    """

    serializer = Serializer(settings.SECRET_KEY, constants.ACCESS_TOKEN_EXPIRES)

    data = {'openid':  openid}

    # 类型 是字节
    token = serializer.dumps(data)

    return token.decode()




