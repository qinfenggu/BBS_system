from django.shortcuts import render
from django.views import View
from django import http
from utils.response_code import RETCODE
from goods.models import SKU
import json
from django_redis import get_redis_connection
import pickle, base64


class CartsView(View):
    """购物车管理"""

    # 加购后保存信息到redis或者cooki里面
    def post(self, request):
        """
        1.接收参数
        2.校验参数
        3.判断用户是否登录
        4.用户已经登录,操作Redis购物车
        5.用户未登陆,操作cookie购物车
        6.响应结果
        """
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')  # count是那个商品规格选项上面那个数量框
        selected = json_dict.get('selected', True)    # 可选参数。如果'selected'在前端传过来的json里面没有它这个key。默认selected为True。
        # 所以默认给这个商品选上

        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('参数sku_id错误')

        try:  # 主要是为了确认传过来的count是一个数字的字符串。如果要是给的是一个字母或者其他字符串就不行
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden('参数count错误')

        if selected:  # 如果selected是Fasle是不会走下面。如果selected是Ture或者是其他东西会走
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected错误')

        user = request.user      # 因为如果登录了肯定存在login(request),如果没有登录那request.user 肯定是None。那么user.is_authenticated:也肯定不存在
        if user.is_authenticated:
            # 用户已经登录
            redis_conn = get_redis_connection('carts')
            # carts_user_id: {sku_id1: count, sku_id3: count, sku_id5: count, ...}
            # 需要以增量计算的形式保存商品数据
            shop = redis_conn.hget('cart_%s' % user.id, sku_id)
            pl = redis_conn.pipeline()
            # if shop:
            #     count = int(shop) + count
            #     redis_conn.hset('cart_%s' % user.id, sku_id, count)
            # else:
            #     redis_conn.hset('cart_%s' % user.id, sku_id, count)
            pl.hincrby('cart_%s' % user.id, sku_id, count)

            if selected:  # 如果selected是False肯定不会报错。保存格式：user.id : {sku_id1, sku_id3, ...}
                pl.sadd('selected_%s' % user.id, sku_id)

            # 执行
            pl.execute()

            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
        else:
            # 用户未登陆
            # 判断cooki里面是否已经有保存carts。如果存在就把新的count+cooki里面旧的'count
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 转成bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 转成bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转成真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

            # cart_dict = {'1': {'count': 10, 'selected': True}, '2': {'count': 20, 'selected': False}}
            if sku_id in cart_dict:
                # 购物车已经存在 增量计算。把新的count+cooki里面旧的'count
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            # 重新组合或新建cart_dict[sku_id]
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # else:
            #     # 创建一个
            #     cart_dict[sku_id] = {
            #         'count': count,
            #         'selected': selected
            #     }

            cart_dict_bytes = pickle.dumps(cart_dict)

            cart_str_bytes = base64.b64encode(cart_dict_bytes)

            cookie_cart_str = cart_str_bytes.decode()

            # 将新的购物车数据写入到cookie中
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

            response.set_cookie('carts', cookie_cart_str)

            return response

    # 显示购物车页面。不管登没登录都可以显示一个加购购物车页面
    def get(self, request):
        """
        不管是从redis还是从cooki里面取。得出向前端传的数据格式都是：
            "sku_id1":{
                "count":"1",
                "selected":"True"
            },
            "sku_id3":{
                "count":"3",
                "selected":"True"
            }
        """

        user = request.user
        if user.is_authenticated:
            # 用户已经登录。在redis里面保存的数据形式： carts_user_id: {sku_id1: count, sku_id3: count, sku_id5: count, ...}
            # 和carts_user_id:{sku_id1， sku_id3， ...}
            redis_conn = get_redis_connection('carts')

            # redis_cart = {sku_id1: count, sku_id3: count, sku_id5: count, ...}或者取不到数据redis_cart=Noen。证明这个用户没有加购任何商品
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)

            # {sku_id1， sku_id3， ...}
            redis_selected = redis_conn.smembers('selected_%s' % user.id)
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_selected
                }
        else:
            # 用户未登陆。在cooki里面保存的数据格式：
            """ 
            "sku_id1":{
                "count":"1",
                "selected":"True"
            },
            "sku_id3":{
                "count":"3",
                "selected":"True"
            }
            """
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 转成bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 转成bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转成真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                #  cart_str = None。证明没有加购任何商品
                cart_dict = {}

        # cart_dict= {sku_id1: {'count': 2, 'selected': True}, sku_id2: {'count': 2, 'selected': True}，..}或者{}
        sku_ids = cart_dict.keys()
        # for sku_id in sku_ids:
        #     sku = SKU.objects.get(id=sku_id)
        # 模型！！！！！
        skus = SKU.objects.filter(id__in=sku_ids)

        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'count': cart_dict.get(sku.id).get('count'),
                'selected': str(cart_dict.get(sku.id).get('selected')),  # 这个是True还是False，主要用于到时结算时
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),
                'amount': str(sku.price * cart_dict.get(sku.id).get('count'))  # 总价。不管 'selected'是True还是False都得算，并不会影响
            })

        context = {
            'cart_skus': cart_skus
        }
        # print(cart_skus)
        return render(request, 'cart.html', context=context)

    def put(self, request):
        """购物车数量的修改"""
        # 当点+或—后，前端那边会先获取当前数量的那个数字然后进行+或—得到结果然触发/carts/的put请求。或者直接输入数字后，直接传这个数字过来给我/carts/的put请求
        # 修改完后得把当前这个商品的购物车新数据传给js那边，它那边会单独对当前这个商品购物车页面进行修改显示。不用返回整体数据因为又不是进行get请求
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)  # 可选参数

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('参数sku_id错误')

        try:
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden('参数count错误')

        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected错误')

        user = request.user
        if user.is_authenticated:
            # 用户已经登录
            redis_conn = get_redis_connection('carts')

            pl = redis_conn.pipeline()

            # 操作hash  覆盖写入的方式
            pl.hset('cart_%s' % user.id, sku_id, count)

            # 操作set
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)

            # 执行
            pl.execute()
            cart_sku = {
                'id': sku_id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price,
                'count': count,
                'amount': sku.price * count,
                'selected': selected
            }
            # 响应结果
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})

        else:
            # 用户未登陆。直接把count和selected给加密后重新进行设置cooki
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 转成bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 转成bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转成真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

            # {3: {'count': 2, 'selected': True}, 5: {'count': 2, 'selected': True}}。要重新把cart_str给解码解密
            # 而不是直接重新cart_dict = {}原因：会把比如对3号商品进行操作的话，如果不加密解密取cart_str而是直接cart_str={}，会把5号商品给整吗，没了。
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            cart_sku = {
                'id': sku_id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price,
                'count': count,
                'amount': sku.price * count,
                'selected': selected
            }
            cart_dict_bytes = pickle.dumps(cart_dict)

            cart_str_bytes = base64.b64encode(cart_dict_bytes)

            cookie_cart_str = cart_str_bytes.decode()
            # 重新写入到cookie中
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})
            response.set_cookie('carts', cookie_cart_str)

            # 响应结果
            return response

    def delete(self, request):
        """删除购物车"""
        # 删除后告诉我成功还是失败。不用返回整体的数据，又不是get请求。
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('参数sku_id错误')

        user = request.user
        if user.is_authenticated:
            # 直接删除redis里面对应的数据
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, sku_id)
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()

            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

        else:
            # 用户未登陆。直接把cooki里面的信息取出来{}，然后根据sku_id ，把它在{}里面对应的数据给删除后成新的{}，把它重新设置cooki
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 转成bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 转成bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转成真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

            # sku_id:3
            # {3: {'count': 2, 'selected': True}, 5: {'count': 2, 'selected': True}}
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

            if sku_id in cart_dict:
                del cart_dict[sku_id]

                cart_dict_bytes = pickle.dumps(cart_dict)

                cart_str_bytes = base64.b64encode(cart_dict_bytes)

                cookie_cart_str = cart_str_bytes.decode()

                # 重新写入到cookie中
                # print(cookie_cart_str)
                response.set_cookie('carts', cookie_cart_str)

                # 响应结果
            return response


class CartsSelectAllView(View):
    """全选购物车"""
    def put(self, request):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected')

        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected错误')

        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')

            # 获取所有的记录  {b'3': b'1', b'4': '2'}
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)

            redis_sku_ids = redis_cart.keys()

            if selected:
                # for redis_sku_id in redis_sku_ids:
                #     redis_conn.sadd('selected_%s' % user.id, redis_sku_id)
                redis_conn.sadd('selected_%s' % user.id, *redis_sku_ids)
            else:
                for redis_sku_id in redis_sku_ids:
                    redis_conn.srem('selected_%s' % user.id, redis_sku_id)

            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

        else:
            cart_str = request.COOKIES.get('carts')

            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

            # cart_str != 'gAN9cQAu':原因，如果COOKIES里面'carts'的值取出来的是一个空{}的话，cart_str = request.COOKIES.get('carts')取出来的
            # 是一个 'gAN9cQAu'
            if cart_str and cart_str != 'gAN9cQAu':
                # 转成bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 转成bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转成真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)

                # cart_dict = {'1': {'count': 10, 'selected': True}, '2': {'count': 20, 'selected': False}}

                for sku_id in cart_dict:
                    cart_dict[sku_id]['selected'] = selected

                cart_dict_bytes = pickle.dumps(cart_dict)

                cart_str_bytes = base64.b64encode(cart_dict_bytes)

                cookie_cart_str = cart_str_bytes.decode()

                # 将新的购物车数据写入到cookie中

                response.set_cookie('carts', cookie_cart_str)

            return response




