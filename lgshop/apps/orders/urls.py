# @ Time    : 2021/1/20 21:57
# @ Author  : JuRan
from django.urls import path, re_path
from . import views

app_name = 'orders'

urlpatterns = [
    # 展示订单
    path('orders/settlement/', views.OrderSettlementView.as_view(), name='settlement'),
    # 提交订单
    path('orders/commit/', views.OrderCommitView.as_view(), name='commit'),
    # 订单提交成功
    path('orders/success/', views.OrderSuccessView.as_view(), name='commit'),
    # 我的订单
    re_path(r'^orders/info/(?P<page_num>\d+)', views.UserOrderInfoView.as_view()),

]