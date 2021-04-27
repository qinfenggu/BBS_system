# @ Time    : 2021/3/31 21:38
# @ Author  : JuRan
import base64, pickle
from django_redis import get_redis_connection


def merge_carts_cookies_redis(request, user, response):
    """
    合并购物车
    相同的商品 用cookie覆盖redis
    redis当中有的 cookie 里面没有 保留redis中的
    勾选状态以cookie为准的

    1.获取cookies中的购物车数据
    2.判断cookies中的购物车数据是否存在
    3.如果存在,需要合并
    4.如果不存在,不需要合并
    5.准备新的{}和[]来保存新的数据  sku_id count selected  unselected
    6.遍历出cookies中的购物车数据
    7.根据新的数据结构,合并到redis中   将cookies中的数据调整成redis中一样
    如果cooki里面sku_1:2,这个用户的redis里也存在sku_1:3，那么会让sku_1:2取代你sku_1:3。
    如果cooki里面sku_1的select是False，但是在用户的redis里面select里面[]存在着sku1，那么就会把这个sku_1从[]里面删除出来
    :return:
    """
    # 获取cookies中的购物车数据，当用户名或QQ登录后把这个购物车数据保存到redis里面，让它属于这个用户redis里面的购物车一员
    cart_str = request.COOKIES.get('carts')

    if not cart_str and cart_str != 'gAN9cQAu':
        return response

    # 转成bytes类型的字符串
    cookie_cart_str_bytes = cart_str.encode()
    # 转成bytes类型的字典
    cookie_cart_dict_bytes = base64.b64decode(cookie_cart_str_bytes)
    # 转成真正的字典
    cookie_cart_dict = pickle.loads(cookie_cart_dict_bytes)

    # {sku_id:count}放到 new_cart_dict   selected=>放到new_selected_add  unselected=>放到 new_selected_rem

    # 为啥需要准备创建新的{}，不直接用cookie_cart_dict ，因为cookie_cart_dict 里面的{sku_id:count，selected：布尔值}
    # 而保存到redis里面的只需{sku_id:count},[sku_id,...]
    new_cart_dict = {}
    new_selected_add = []
    new_selected_rem = []

    # cart_dict = {'1': {'count': 10, 'selected': True}, '2': {'count': 20, 'selected': False}}

    for sku_id, cookie_dict in cookie_cart_dict.items():
        new_cart_dict[sku_id] = cookie_dict['count']

        if cookie_dict['selected']:
            new_selected_add.append(sku_id)
        else:
            new_selected_rem.append(sku_id)

    # 写入到redis
    redis_conn = get_redis_connection('carts')

    pl = redis_conn.pipeline()
    # hmset创建或者是继续添加。-
    # 就算new_cart_dict{sku1：2, ...}在redis里面已经存在sku_1:1，那么会去重覆盖让新的sku1：2取代sku_1:1
    pl.hmset('cart_%s' % user.id, new_cart_dict)

    if new_selected_add:
        pl.sadd('selected_%s' % user.id, *new_selected_add)

    if new_selected_rem:
        #  new_selected_rem = []作用，如果某个购物车商品在cooki里面是没有把选择的即select为flase，
        # 而在这个用户redis里面也有这个购物车商品但是select是True，那么就以cooki的为准，把这个商品的sku_id从[]里面取掉
        pl.srem('selected_%s' % user.id, *new_selected_rem)

    pl.execute()

    # 删除cookies。如果不删，你没有关闭浏览器，然后你退出登录，再登录上，它会再次有东西给你合并。所以删掉，合并一次就够了
    response.delete_cookie('carts')

    return response

