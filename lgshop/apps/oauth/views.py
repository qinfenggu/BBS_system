from django.shortcuts import render, redirect
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django import http
from utils.response_code import RETCODE
import logging
from .models import OAuthQQUser
from django.contrib.auth import login
from .utils import generate_access_token, check_access_token
from django_redis import get_redis_connection
from users.models import User

# 创建日志输出器
logger = logging.getLogger('django')


class QQAuthUserView(View):
    """处理QQ登录回调，即扫码或QQ登录后的情况"""

    def get(self, request):
        """处理QQ登录回调的业务逻辑"""
        code = request.GET.get('code')
        if not code:
            return http.HttpResponseForbidden('获取code失败')

        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                            redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            # 使用code获取access_token
            access_token = oauth.get_access_token(code)
            # 使用access_token获取openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('OAuth2.0认证失败')

        # openid ：就是腾讯它数据库那边的QQ用户的ID
        # 使用openid判断该QQ用户是否绑定商城的用户
        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果没有找到记录 openid 未绑定商城用户  展示绑定页面
            # openid 是明文  Sdasdasdasdasy7iyw432 => 明文  可逆 签名的算法
            context = {'access_token_openid': generate_access_token(openid)}
            return render(request, 'oauth_callback.html', context=context)
        else:
            # 找到记录  登录
            # 状态保持
            login(request, oauth_user.user)

            next = request.GET.get('state')

            response = redirect(next)

            response.set_cookie('username', oauth_user.user.username, max_age=3600 * 24)

            # 响应结果 重定向到首页
            return response

    def post(self, request):
        """实现绑定用户的业务逻辑"""
        # 接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code_client = request.POST.get('sms_code')
        access_token = request.POST.get('access_token_openid')

        # 校验参数
        # 判断短信验证码是否一致
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        if sms_code_server is None:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '无效的短信验证码'})

        if sms_code_client != sms_code_server.decode():
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '输入短信验证码有误'})

        # 判断access_token过期了没有即openid是否
        # 有效
        openid = check_access_token(access_token)
        if not openid:
            return render(request, 'oauth_callback.html', {'openid_errmsg': 'openid已经失效'})

        # 使用手机号查询对应的用户是否存在
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果不存在, 创建一个新的用户
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
        else:
            # 如果存在,校验密码
            if not user.check_password(password):
                return render(request, 'oauth_callback.html', {'account_errmsg': '账号或者密码错误'})

        # 绑定用户
        # oauth_qq_user = OAuthQQUser(user=user, openid=openid)
        # oauth_qq_user.save()
        try:
            oauth_qq_user = OAuthQQUser.objects.create(user=user, openid=openid)
        except Exception as e:
            return render(request, 'oauth_callback.html', {'account_errmsg': '账号或者密码错误'})

        # 登录后把cooki里面的购物车添加到这个用户的redis里面
        from carts.utils import merge_carts_cookies_redis
        merge_carts_cookies_redis(request, user, response)

        # 重定向到首页
        # 状态保持。
        login(request, oauth_qq_user.user)

        next = request.GET.get('state')
        # print(next)
        response = redirect(next)

        response.set_cookie('username', oauth_qq_user.user.username, max_age=3600 * 24)
        # 响应结果 重定向到首页
        return response


class QQAuthURLView(View):
    """提供QQ登录扫码页面"""

    def get(self, request):

        next = request.GET.get('next')

        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)

        # 生成扫描链接地址
        login_url = oauth.get_qq_url()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})

# http://www.meiduo.site:8000/oauth_callback?code=E48B6F743D1543BA0A4536CA775EE562&state=%2F
