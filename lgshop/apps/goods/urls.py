# @ Time    : 2021/1/22 22:08
# @ Author  : JuRan
from django.urls import path, re_path
from . import views


app_name = 'goods'

urlpatterns = [
    # 商品列表页面
    re_path(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.GoodsListView.as_view(), name='list'),
    # 商品热销排行
    re_path(r'^hot/(?P<category_id>\d+)', views.HotGoodsView.as_view()),
    # 商品详情页
    re_path(r'^detail/(?P<sku_id>\d+)', views.DetaiGoodslView.as_view(), name='detail'),
    # 统计商品的访问量
    re_path(r'^detail/visit/(?P<category_id>\d+)/$', views.DetailVisitView.as_view())
]