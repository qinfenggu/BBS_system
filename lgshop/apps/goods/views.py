from django.shortcuts import render
from django.views import View
from contents.utlis import get_categories
from .models import GoodsCategory, SKU, SPUSpecification, SKUSpecification, GoodsVisitCount
from django import http
from .utils import get_breadcrumb
# 先规定每页多少字,然后得出一共多少页
from django.core.paginator import Paginator
from utils.response_code import RETCODE
from django.utils import timezone


class HotGoodsView(View):
    """热销排行"""
    # 每次进入列表页面或者商品详情页面同时，就会自动触发这个视图而且给前端传递热销商品对象
    def get(self, request, category_id):
        # 查询指定分类(category_id), 必须是上架商品 按照销量从高到底排序 取前2位
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]
        # 模型转字典列表
        hot_skus = []
        for sku in skus:
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url
            }
            hot_skus.append(sku_dict)

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})


class GoodsListView(View):
    """商量列表页面"""

    def get(self, request, category_id, page_num):

        # category_id 参数校验。
        """
        首先点首页级别分类栏进列表页面来、从列表页面点它本身级别分类栏
        或者从列表页面它本身点'默认'、'价格','人气'、点分页导航发起请求
         """
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return http.HttpResponseForbidden('参数category_id不存在')

        # 获取sort排序 ?sort=juran
        sort = request.GET.get('sort', 'default')
        if sort == 'price':

            sort_field = 'price'
        elif sort == 'hot':
            sort_field = 'sales'
        else:
            sort = 'default'
            sort_field = 'create_time'

        # 查询三级分类数据。这个是为了让列表页面显示级别分类栏
        categories = get_categories()
        # 查询面包屑。这个是为了，显示那个：手机>手机通讯>手机；手机>手机通讯 这种叫面包屑导航功能
        breadcrumb = get_breadcrumb(category)

        # 分页和排序。根据category.id，sort_field查询符合条件的商品
        skus = SKU.objects.filter(is_launched=True, category_id=category.id).order_by(sort_field)
        # print(skus)

        # Paginator('要分页的数据', '每页记录的条数')
        pageinator = Paginator(skus, 5)  # 把skus进行分页 ,每页5条记录

        try:
            # 获取用户当前要看的那一页数据
            page_skus = pageinator.page(page_num)
        except Exception as e:
            return http.HttpResponseNotFound('Empty Page')

        # 总页数
        total_page = pageinator.num_pages

        # breadcrumb = {
        #     'cat1': category.parent.parent,
        #     'cat2': category.parent,
        #     'cat3': category
        # }

        context = {
            'categories': categories,    # 三级分类数据
            'breadcrumb': breadcrumb,    # 面包屑数据
            'page_skus': page_skus,      # 当前页商品sku数据
            'total_page': total_page,    # 一个可分多少页
            'sort': sort,                # 按什么排序显示，价格还是热度
            'category_id': category_id,  # 当前频道组id
            'page_num': page_num         # 当前页码
        }
        return render(request, 'list.html', context=context)



"""
# 按照商品创建时间排序
http://www.meiduo.site:8000/list/115/1/?sort=default
# 按照商品价格由低到高排序
http://www.meiduo.site:8000/list/115/1/?sort=price
# 按照商品销量由高到低排序
http://www.meiduo.site:8000/list/115/1/?sort=hot
# 用户随意传排序
http://www.meiduo.site:8000/list/115/1/?sort=juran
"""


class DetaiGoodslView(View):
    """商品详情页"""

    def get(self, request, sku_id):
        # print('sku_id:', sku_id)
        # 验证sku_id存不存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            # return http.HttpResponseForbidden
            return render(request, '404.html')

        # 查询三级类别数据
        categories = get_categories()
        # 查询面包屑数据
        breadcrumb = get_breadcrumb(sku.category)

        # SKUSpecification模型表是一个中间表，可以查询当前商品所拥有的的规格选项和规格选项的参数
        # 当前sku id为1的默认的规格。下面这个查询语句是查询当前商品比如华为 mate10 65Gxxxxxxxx所拥有的全部规格选项
        sku_specs = SKUSpecification.objects.filter(sku__id=sku_id).order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            # ku_specs是规格选项，上面查询得出很多规格选项，所以它是ku_specs规格选项是一个列表。spec.option.id规格id
            sku_key.append(spec.option.id)
        # [1, 4, 7]
        # print(sku_key)

        # 获取当前商品的所属的spu。即华为 mate10 65Gxxxxxxxx所属spu是华为
        # print('sku_key:', sku_key)
        spu_id = sku.spu_id
        # print('spu_id:', spu_id)
        # 获取当前spu即华为所有的sku
        skus = SKU.objects.filter(spu_id=spu_id)
        # print('skus:', skus)

        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数。因为SPUSpecification这个模型表是所有的规格参数表，在创建这个模型时
            # sku = models.ForeignKey(SKU, related_name='specs', on_delete=models.CASCADE, verbose_name='sku')
            # 所以可以s.specs。这个 s_specs就是这个华为所有商品全部规格选项
            # print('s.specs:', s.specs)
            s_specs = s.specs.order_by('spec_id')

            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # print(spec_sku_map)

        # 获取当前商品的规格信息
        goods_specs = SPUSpecification.objects.filter(spu_id=spu_id).order_by('id')
        # print(goods_specs)
        # 若当前sku的规格信息不完整，则不再继续
        # if len(sku_key) < len(goods_specs):
        #     return

        for index, spec in enumerate(goods_specs):
            # print(index, spec)
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                # [1,4,7]
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

        context = {
            'categories': categories,   # 三级类别数据
            'breadcrumb': breadcrumb,   # 面包屑
            'sku': sku,                 # 当前页面所有商品sku
            'specs': goods_specs        # 当前商品规格和规格参数
        }

        return render(request, 'detail.html', context=context)


class DetailVisitView(View):
    """统计分类商品的访问量"""
    # 当进入一个商品的详情页面后，就会自动触发post请求从而触发这个视图。category_id这个参数在js里面请求来了的
    def post(self, request, category_id):
        # 校验参数
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return http.HttpResponseForbidden('category_id不存在')
        # 获取当前的日期
        t = timezone.localtime()
        # print(t)    2021-03-26 13:29:58.365797+00:00
        # 获取当前的时间字符串
        today_str = '%d-%02d-%02d' % (t.year, t.month, t.day)

        try:
            # 存在记录  修改记录 count。用get不用filter原因：用filter就算查询不到数据，也是不会抛出异常错误的。用get就会
            counts_data = GoodsVisitCount.objects.get(date=today_str, category=category.id)
        except GoodsVisitCount.DoesNotExist:
            # 不存在记录 新增。这样子写的原因，这样子就可以复用了counts_data了。不管存不存在记录，最后保存数据都用counts_data
            counts_data = GoodsVisitCount()

        # 。下面这个和 GoodsVisitCount(category=value)其实是一样的
        try:
            counts_data.category = category
            counts_data.count += 1
            counts_data.date = today_str
            counts_data.save()
        except Exception as e:
            return http.HttpResponseServerError('统计失败')

        # 响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})