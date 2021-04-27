# @ Time    : 2021/1/25 20:49
# @ Author  : JuRan
from django.urls import path, re_path
from . import views


urlpatterns = [
    # 图形验证码 \w  [A-Za-z0-9_]-  uuid 78b4d5b7-5157-4b2a-bf48-ba616e169d66
    re_path(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageCodeView.as_view()),
    re_path(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),
]