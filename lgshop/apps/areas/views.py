from django.shortcuts import render
from django.views import View
from .models import Area
from django import http
from utils.response_code import RETCODE
from django.core.cache import cache


class AreasView(View):
    """省市区三级联动"""
    def get(self, request):
        # 判断当前是要查询省份数据还是市区数据
        area_id = request.GET.get('area_id')
        # 刚进'收货地址'页面后，就会触发area请求。显示所有省份
        if not area_id:
            # r = get_redis_connection('xxxx')
            # r.setex
            # 看是否前面已经把省份查询过一遍保存到redis里面了。有就直接返回，不用再查询一次了
            province_list = cache.get('province_list')
            if not province_list:
                # 做try异常处理。防止万一查询不出来
                try:
                    # 查询所有省份数据   province_list就是一个所有{省份id：省份名}列表
                    province_model_list = Area.objects.filter(parent_id__isnull=True)
                    province_list = []
                    for province_model in province_model_list:
                        province_dict = {
                            "id": province_model.id,
                            "name": province_model.name
                        }
                        province_list.append(province_dict)

                    # 将数据缓存到redis默认的那个数据库里面，默认的数据库是哪个，看配置文件。本项目默认是下划线0那个数据库
                    cache.set('province_list', province_list, 3600)
                except Exception as e:
                    return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '查询省份数据错误'})
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
        # 点进'新增收货地址'页面后，点选择省份下拉框选择（比如选择'北京省'）完成后就会就会触发area_id请求。以此类推点选择市份下拉框选择也是
        else:
            # 看是否前面已经把市区查询过一遍保存到redis里面了。有就直接返回，不用再查询一次了
            sub_data = cache.get('sub_area_' + area_id)
            if not sub_data:
                # 做try异常处理。防止万一查询不出来
                try:
                    # 一查多  area_id = 1300000。先查询的是省
                    parent_model = Area.objects.get(id=area_id)
                    # 查询拿这个省id作为外键的所有数据。即这个省下的所有市。
                    sub_model_list = parent_model.subs.all()

                    subs = []
                    for sub_model in sub_model_list:
                        sub_dict = {
                            'id': sub_model.id,
                            'name': sub_model.name
                        }
                        subs.append(sub_dict)

                    sub_data = {
                        'id': parent_model.id,        # 省id或市id
                        'name': parent_model.name,    # 省份名或市名
                        'subs': subs                  # subs就是一个所有{市id：市名}或{区id：区名}列表。
                    }
                    cache.set('sub_area_' + area_id, sub_data, 3600)
                except Exception as e:
                    return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '查询市区数据错误'})
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})




