# @ Time    : 2021/1/20 21:57
# @ Author  : JuRan
from django.urls import path, re_path
from . import views

app_name = 'users'

urlpatterns = [
    # 注册
    path('register/', views.RegisterView.as_view(), name='register'),
    # 判断注册时，输入的用户名是否重复所请求的URL
    re_path(r'^usernames/(?P<username>[a-zA-Z0-9-_]{5,20})/count/$', views.UsernameCountView.as_view()),
    # 判断注册时，输入的手机号是否重复所请求的URL
    path('mobile/<mobile>/', views.MobileCountView.as_view(), name='mobile'),
    # re_path(r'^mobile/(?P<mobile>1[3456789]\d{9}$)/count/$', views.MobileCountView.as_view())
    # 用户登录
    path('login/', views.LoginView.as_view(), name='login'),
    # 退出登录
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # 个人中心
    path('info/', views.UserInfoView.as_view(), name='info'),
    # 保存邮箱
    path('email/', views.EmailView.as_view()),
    # 验证邮箱
    path('emails/verification/', views.VerifyEmailView.as_view()),
    # 展示用户地址
    path('addresses/', views.AddressView.as_view(), name='address'),
    # 新增收货地址
    path('addresses/create/', views.AddressCreateView.as_view()),
    # 修改地址
    re_path(r'addresses/(?P<address_id>\d+)/$', views.UpdateDestoryAddressView.as_view()),
    # 修改默认地址
    re_path(r'addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view()),
    # 修改标题
    re_path(r'addresses/(?P<address_id>\d+)/title/$', views.UpdateTitleAddressView.as_view()),
    # 修改密码
    path('change_password/', views.ChangePasswordView.as_view(), name='change_password'),
    # 用户浏览记录、
    path('browse_histories/', views.UserBrowseHistory.as_view()),
    # 我的订单
    re_path(r'/orders/info/(?P<page_num>\d+)/', views.UserOrderInfoView.as_view())
]