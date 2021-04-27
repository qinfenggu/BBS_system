from django.shortcuts import render, redirect, reverse
from django.views import View
from django import http
from .forms import RegisterForm, LoginForm
from .models import User, Address
from django.contrib.auth import login, authenticate, logout
from django_redis import get_redis_connection
from django.contrib.auth.hashers import check_password
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.mixins import LoginRequiredMixin
from utils.views import LoginRequiredJsonMinin
from celery_tasks.email.tasks import send_verify_email
from .utils import generate_verify_email_url, check_verify_email_token
from utils.response_code import RETCODE
from . import constants
import json
import re
import logging
from goods.models import SKU
from carts.utils import merge_carts_cookies_redis

logger = logging.getLogger('django')


# 注册
class RegisterView(View):

    def get(self, request):
        """提供用户注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """提供用户注册逻辑"""
        # 校验参数
        register_form = RegisterForm(request.POST)

        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            password = register_form.cleaned_data.get('password')
            mobile = register_form.cleaned_data.get('mobile')

            # 判断短信验证码是否与保存到redis里面的一致
            sms_code_client = register_form.cleaned_data.get('sms_code')
            redis_con =get_redis_connection('verify_code')
            sms_code_server = redis_con.get('sms_%s' % mobile)
            if sms_code_server is None:
                return render(request, 'register.html', {'sms_code_errmsg':'短信验证码已失效'})

            if sms_code_server.decode() != sms_code_client:
                return render(request, 'register.html', {'sms_code_errmsg': '输入短信验证码有误'})

            # 保存到数据库中。
            try:
                user = User.objects.create_user(username=username, password=password, mobile=mobile)
            except Exception as e:
                return render(request, 'register.html', {'register_errmsg': '注册失败'})

            # 状态保持
            login(request, user)
            # 响应结果
            print('注册成功！！')
            response = redirect(reverse('contents:index'))
            # 设置cookie
            response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
            return response
        else:
            print(register_form.errors.get_json_data())
            context = {
                'forms_errors': register_form.errors
            }
            return render(request, 'register.html', context=context)


# 注册输入用户名，光标离开用户名输入框后，发起这个^usernames/(?P<username>[a-zA-Z0-9-_]{5,20})/count/$请求
class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        """
        :param username: 用户名
        :return: 返回用户名是否重复  JSON
        """

        count = User.objects.filter(username=username).count()

        return http.JsonResponse({'code': 200, 'errmsg': 'OK', 'count': count})


# 注册输入手机号，光标离开手机号输入框后，发起这个^mobile/(?P<mobile>1[3-9]\d{9}${5,20})/count/$请求
class MobileCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, mobile):
        """
        :param username: 用户名
        :return: 返回用户名是否重复  JSON
        """

        count = User.objects.filter(mobile=mobile).count()

        return http.JsonResponse({'code': 200, 'errmsg': 'OK', 'count': count})


class LoginView(View):
    def get(self, request):
        """
        提供登录页面
        :return:
        """
        return render(request, 'login.html')

    def post(self, request):
        """
        实现登录逻辑
        :param request:
        :return:
        """
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            remembered = login_form.cleaned_data.get('remembered')

            if not all([username, password]):
                return http.HttpResponseForbidden('缺少必传参数')

            # 认证登录用户
            # user = User.objects.get(username=username)
            # pwd = user.password     # 从数据库里面取出这个密文

            # if check_password(password, pwd):

            # 验证登录用户。验证不通过user就是一个None，验证通过就是
            user = authenticate(username=username, password=password)
            if user is None:
                return render(request, 'login.html', {'account_errmsg': '账号或密码错误'})
            # 保持状态
            login(request, user)
            print('已经登录验证成功了！！')
            print('request.user.name:', request.user.username)

            if remembered:
                # 浏览器关闭就销毁session
                request.session.set_expiry(0)
            else:
                # session默认状态保持两周
                request.session.set_expiry(None)
            next = request.GET.get('next')
            if next:
                response = redirect(next)
            else:
                response = redirect(reverse('contents:index'))
            # 登录时用户名写入到cookie，有效期15天
            response.set_cookie('username', user.username, max_age=3600 * 24 * 15)

            # 登录成功后合并存在cooki里面的购物车到这个用户的redis里面的购物车去。原先的response里面是保存着用户登录信息和购物车信息的response
            # 现在这个返回的这个response是保存着用户登录信息（购物车信息已经被删除了）
            response = merge_carts_cookies_redis(request, user, response)

            return response
        else:
            print(login_form.errors.get_json_data())
            context = {
                'forms_errors': login_form.errors
            }
            return render(request, 'login.html', context=context)


class LogoutView(View):
    """用户退出登录"""

    def get(self, request):
        """实现用户退出登录的逻辑"""
        # 清除状态保持信息
        logout(request)

        # 重定向
        response = redirect(reverse('contents:index'))

        # 删除cookie
        response.delete_cookie('username')

        return response


class UserInfoView(LoginRequiredJsonMinin, View):
    """用户个人中心"""
    # login_url = '/users/login/'

    def get(self, request):
        print(request)
        """提供用户个人页面"""
        # 优化的地方
        # if request.user.is_authenticated:
        #     # 已经登录
        #     return render(request, 'user_center_info.html')
        # else:
        #     # 未登陆
        #     return redirect(reverse('users:login'))
        # http://127.0.0.1:8000/users/login/?next=/users/info/
        # LOGIN_URL = '/accounts/login/'    # 没有登录跳转的链接
        # REDIRECT_FIELD_NAME = 'next'      #  没有登录要访问的链接的参数
        # login_url = '/users/login/'
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email':request.user.email,
            'email_active':request.user.email_active,
        }
        return render(request, 'user_center_info.html', context=context)


class EmailView(LoginRequiredJsonMinin, View):
    """添加邮箱"""
    # 没有登录就可以访问

    def put(self, request):
        # 接收参数。put方法前端传过来的数据格式：b'{key:value}'。所以需要decode。loads是把json类型转成字典
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        email = json_dict.get('email')

        # 校验参数
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数邮箱有误')

        # 存数据
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})
        # 发送邮件
        # subject = "商城邮箱验证"
        # html_message = '<p>尊敬的用户您好！</p>' \
        #                '<p>感谢您使用商城。</p>' \
        #                '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
        #                '<p><a href="%s">%s<a></p>' % (email, 'www.baidu.com', 'www.baidu.com')

        # send_mail(subject, '', from_email=settings.EMAIL_FROM, recipient_list=[email], html_message=html_message)
        # 生成激活链接
        verify_url = generate_verify_email_url(request.user)
        # 发送邮件
        send_verify_email.delay(email, verify_url)

        # 响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class VerifyEmailView(View):
    """验证邮箱"""

    def get(self, request):
        # 接收
        token = request.GET.get('token')
        print('token:', token)

        if not token:
            return http.HttpResponseForbidden('缺少token')
        # 解密 token => user {'user_id': 1, 'email': 'xxxx@qq.com'}
        # 查询用户
        user = check_verify_email_token(token)
        if user.email_active == 0:
            # 没有激活 email_active 设置为true
            user.email_active = True
            user.save()
        else:
            # email_active 是否已经激活
            return http.HttpResponseForbidden('邮箱已经被激活')

        # 响应结果
        return redirect(reverse('users:info'))


class AddressView(LoginRequiredMixin, View):
    """用户收货地址"""

    def get(self, request):
        """提供收货地址界面"""

        # 查询当前用户所属的所有收货地址
        addresses = Address.objects.filter(user=request.user, is_deleted=False)
        address_list = []
        for address in addresses:
            address_dict = {
                'id': address.id,
                "title": address.title,
                "receiver": address.receiver,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'mobile': address.mobile,
                'tel': address.tel,
                'email': address.email
            }
            address_list.append(address_dict)
        context = {
            'addresses': address_list,
            'default_address_id': request.user.default_address.id  # request.user.default_address_id
        }

        return render(request, 'user_center_site.html', context=context)


class AddressCreateView(LoginRequiredJsonMinin, View):
    """新增地址"""

    def post(self, request):
        """新增地址逻辑"""

        # 判断用户地址已经创建的收货地址是否超过上限：限制可创建收货地址数量
        count = Address.objects.filter(user=request.user).count()
        if count > constants.USER_ADDRESS_COUNTS_LIMT:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超出用户地址上限'})
        # 接收参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 保存用户传入的数据
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email,
            )
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})

        address_dict = {
            'id': address.id,
            "title": address.title,
            "receiver": address.receiver,
            'province': address.province.name,
            'city': address.city.name,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }
        # 判断当前用户是否有默认收货地址，如果没有就设置一个
        if not request.user.default_address:
            request.user.default_address = address
            request.user.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})


class UpdateDestoryAddressView(LoginRequiredJsonMinin, View):
    """更新和删除地址"""
    # 通过前端那边<a class="edit_icon" @click="show_edit_site(index)">编辑</a>点击事件，触发js那边的show_edit_site方法。
    # 而这个方法触发put请求
    def put(self, request, address_id):
        # 接收参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 更新数据
        # address = Address.objects.get(id=address_id)
        # address.title = receiver
        # address.save()
        try:
            # update 返回受影响的行数
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email,
            )
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '修改地址失败'})

        address = Address.objects.get(id=address_id)

        address_dict = {
            'id': address.id,
            "title": address.title,
            "receiver": address.receiver,
            'province': address.province.name,
            'city': address.city.name,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }
        # 响应新的地址给前端渲染
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改地址成功', 'address': address_dict})

    # 通过前端那边<span class="del_site" @click="delete_address(index)">×</span>点击事件，触发js那边的delete_address方法。
    # 而这个方法触发delete请求
    def delete(self, request, address_id):
        """删除地址"""
        # 逻辑删除(修改 is_deleted=True) 还是 物理删除
        try:
            address = Address.objects.get(id=address_id)
            address.is_deleted = True
            address.save()
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})


class DefaultAddressView(View):
    """设置默认地址"""
    def put(self, request, address_id):
        # 用户表 default_address
        try:
            # , user=request.user
            address = Address.objects.get(id=address_id)
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


class UpdateTitleAddressView(LoginRequiredJsonMinin, View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置地址标题失败'})

        # 4.响应删除地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置地址标题成功'})


class ChangePasswordView(LoginRequiredJsonMinin, View):
    """修改密码"""

    def get(self, request):
        """展示修改密码界面"""
        return render(request, 'user_center_pass.html')

    def post(self, request):
        """实现修改密码逻辑"""
        # 接收参数
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password2 = request.POST.get('new_password2')

        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            result = request.user.check_password(old_password)
            if not result:
                return render(request, 'user_center_pass.html', {'origin_pwd_errmsg':'原始密码错误'})
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg':'原始密码错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        if new_password != new_password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')

        # 修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '修改密码失败'})

        # 清理状态保持信息
        logout(request)
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')

        # # 响应密码修改结果：重定向到登录界面
        return response


class UserBrowseHistory(LoginRequiredJsonMinin, View):
    """用户浏览记录"""
    # 进入商品详情页面后，会触发这个请求post请求从而执行这个post方法
    def post(self, request):
        """保存用户浏览记录"""
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        sku_id = json_dict.get('sku_id')

        # 校验参数
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id不存在')

        redis_conn = get_redis_connection('history')
        user = request.user
        pl = redis_conn.pipeline()
        # 去重复。先查看redis里面有没有user.id这个key。如果有就查看这个key的[]里面有没有存在sku_id元素，如果有全部删除
        pl.lrem('history_%s' % user.id, 0, sku_id)
        # 保存。然后把sku_id保存进来。lpush是新保存的数据在最左边
        pl.lpush('history_%s' % user.id, sku_id)
        # 截取。保存进来后，只保留左边前5个，弄成新的key新的[]
        pl.ltrim('history_%s' % user.id, 0, 4)
        print('浏览记录保存成功！！')
        # 执行
        pl.execute()

        # 响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

    # 进入用户个人中心后，触发这个get请求从而执行这个get方法
    def get(self, request):
        """展示用户商品浏览器记录"""

        redis_conn = get_redis_connection('history')
        user = request.user
        sku_ids = redis_conn.lrange('history_%s' % user.id, 0, -1)
        # print(sku_ids)

        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url,

            })

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': skus})


class UserOrderInfoView(LoginRequiredJsonMinin, View):
    """我的订单"""

    def get(self, request, page_num):
        """提供我的订单页面"""
        pass

        # 查询订单

        # 遍历所有订单
        # 分页