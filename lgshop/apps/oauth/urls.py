# @ Time    : 2021/2/3 20:35
# @ Author  : JuRan
from django.urls import path, re_path
from . import views


urlpatterns = [
    # 提供QQ登录扫描页面
    path('qq/login/', views.QQAuthURLView.as_view()),
    path('oauth_callback/', views.QQAuthUserView.as_view()),
]