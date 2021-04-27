from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from utils.views import LoginRequiredJsonMinin
from users.models import Address
from django_redis import get_redis_connection
from goods.models import SKU
from .models import OrderInfo, OrderGoods
from django import http
from utils.response_code import RETCODE
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
import time
import json


class OrderSettlementView(LoginRequiredJsonMinin,View):
    """结算订单"""

    def get(self, request):

        # 查询用户收货地址(没有被删除的)。如果查询不到，证明这个用户没有收货地址就给前端显示None就行
        user = request.user
        try:
            addresses = Address.objects.filter(user=user, is_deleted=False)
        except Exception as e:
            addresses = None

        redis_conn = get_redis_connection('carts')
        # 先把这个用户的购物车所有商品sku_id查询出来。比如{sku_1:3,sku_2:1,sku_3:6,...}。是为了求被勾选商品数量
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)

        # 把当前用户哪些购物车被勾选select的商品查询出来。[sku_1, sku_2]。为了求被勾选的商品
        redis_selected = redis_conn.smembers('selected_%s' % user.id)

        # 新建一个{}，弄成{被勾选商品sku_id:数量}
        new_cart_dict = {}
        for sku_id in redis_selected:
            # 从redis里面取出来的数据是字节
            new_cart_dict[int(sku_id)] = int(redis_cart[sku_id])

        # 把新建的{},把它里面的key都取出来，这些key其实就是被勾选的sku_id
        sku_ids = new_cart_dict.keys()

        skus = SKU.objects.filter(id__in=sku_ids)

        total_count = 0
        total_amount = 0
        # 计算商品总数量和总共价格。
        # from decimal import Decimal  Decimal这个是一个类型浮动型的数据类型
        for sku in skus:
            # 给sku添加count和amount
            sku.count = new_cart_dict[sku.id]
            sku.amount = sku.price * sku.count

            total_count += sku.count
            total_amount += sku.amount

        # 运费固定12块钱
        freight = 12
        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,   # 购物车商品总件数
            'total_amount': total_amount,    # 总金额
            'freight': freight,          # 运费
            'payment_amount': total_amount + freight       # 实际付款
        }

        return render(request, 'place_order.html', context=context)


class OrderCommitView(LoginRequiredJsonMinin, View):
    """提交订单"""
    # 点'提交订单后就会触发/orders/commit/这个url，从而触发这个post方法。当这个post方法完成后，会把
    # return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'order_id': ''})格式是数据返回给js那边，那边会接着触发
    # 'orders/success/'这个视图，从而会展示提交订单成功页面

    def post(self, request):
        """保存订单基本信息和订单商品信息"""
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')

        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('参数address_id错误')

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.HttpResponseForbidden('参数pay_method错误')

        # 开启事务。如果sku、spu、OrderInfo、OrderGoods这四张表任意一张表保存数据过程失败了。就给我全部回滚。
        with transaction.atomic():
            # 设置保存点即保存数据库最初的状态
            save_id = transaction.savepoint()
            try:
                # 保存订单基本信息
                # 订单编号规则： 时间 + 用户id  1 2 3  20200402210122 + 0000000001
                user = request.user
                order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

                # 把订单信息保存到数据库里面
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=0,
                    freight=12,
                    pay_method=pay_method,
                    # 如果选择的支付方式是支付宝，那么状态是待支付；选择是货到付款，那么状态是待发货
                    status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY'] else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )

                redis_conn = get_redis_connection('carts')
                # 先把这个用户的购物车所有商品sku_id查询出来。比如{sku_1:3,sku_2:1,sku_3:6,...}。是为了求被勾选商品数量
                redis_cart = redis_conn.hgetall('cart_%s' % user.id)
                # 把当前用户哪些购物车被勾选select的商品查询出来。[sku_1, sku_2]。为了求被勾选的商品
                redis_selected = redis_conn.smembers('selected_%s' % user.id)

                # 新建一个{}，弄成{被勾选商品sku_id:数量}
                new_cart_dict = {}
                for sku_id in redis_selected:
                    new_cart_dict[int(sku_id)] = int(redis_cart[sku_id])
                # 把新建的{},把它里面的key都取出来，这些key其实就是被勾选的sku_id
                sku_ids = new_cart_dict.keys()

                # 因为提交订单里面的商品可不止一件，需要循环每一件商品
                for sku_id in sku_ids:

                    # 如果某个商品它的sku库存进行减少时，核对原来信息不上就返回到这份while进行重新计算
                    # 直到可以减少修改为止。以及对sku、spu、OrderGoods这三张表数量修改成功后就退出这个while循环
                    while True:
                        sku = SKU.objects.get(id=sku_id)
                        # 查询得出当前商品购买数量
                        sku_count = new_cart_dict[sku.id]

                        # 获取没提交订单成功前该商品sku的库存和销量
                        origin_stock = sku.stock
                        origin_sales = sku.sales

                        # 判断当前购买的商品数量是否大于库存
                        if sku_count > origin_stock:
                            # 如果当前购买的商品数量大于库存，上面对数据库的增删改全部给我回滚
                            transaction.savepoint_rollback(save_id)
                            return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})

                        time.sleep(2)  # 这个是模拟网络延迟的。可以删掉。

                        # 第一种写法：商品sku库存减少 ，销量增加
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()

                        # 第二种写法：商品sku库存减少 ，销量增加
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count
                        # 采用这个写法原因：这是乐观锁。改数据之前，先数据库查看一下数据有没有变化，如果没有证明没有人操作。可以现在修改。
                        # 如果变化了证明前n秒之前已经被人抢先有人下单成功了。那么这个语句就不会执行成功了
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)

                        # 返回0 表示 资源抢夺。即在修改之前去核对表信息，发现变化了。既然发现变化，那我对这个商品进行重新的一次运算。
                        # 即跳回到while那边重新执行，直到我抢占为止即可以修改数据为止
                        if result == 0:
                            # 库存10 要买1个  但是下单的时候 有资源抢夺 被买走一个 还剩9个,如果库存满足的话   继续下单,直到库存不足
                            # return http.JsonResponse('下单失败')
                            continue

                        # SPU 销量增加。比如华为 10 mate xxx卖出去了。那么华为这个spu销量增加一下吧
                        sku.spu.sales += sku_count
                        sku.spu.save()

                        # 把订单商品信息保存到数据库里面
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price
                        )

                        # sku_count当前购买所有商品的总数量。保存修改购买所有商品的总数量
                        order.total_count += sku_count
                        order.total_amount += sku_count * sku.price

                        # 下单成功
                        break

                # 保存修改购买所有商品的总价
                order.total_amount += order.freight
                order.save()

            except Exception as e:
                # 如果上面代码报错，也全部给我回滚
                transaction.savepoint_rollback(save_id)
                return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '下单失败'})

        # 提交事务
        transaction.savepoint_commit(save_id)

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'order_id': ''})


class OrderSuccessView(View):
    """订单提交成功"""

    # 上面提交订单post请求结束后，它的js那边会接着触发'orders/success/'这个url，从而展示这个提交订单成页面
    def get(self, request):
        order_id = request.GET.get('order_id')
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_method')
        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }
        print("订单号：", order_id)
        return render(request, 'order_success.html', context)


class UserOrderInfoView(LoginRequiredJsonMinin, View):
    """我的订单。这部分自己做的，没有很完善"""

    def get(self, request, page_num):
        """提供我的订单页面"""
        pass
#
#         user = request.user
#         # 查询订单
#         orders = OrderInfo.objects.filter(user=user)
#
#         # 遍历所有订单
#         order_list = []
#         for order in orders:
#             order_list.append(order)
#
#         # 分页   Paginator('要分页的数据', '每页记录的条数')
#         pageinator = Paginator(order_list, 3)  # 把skus进行分页 ,每页5条记录
#
#         try:
#             # 获取用户当前要看的那一页数据
#             page_orders = pageinator.page(page_num)
#         except Exception as e:
#             return http.HttpResponseNotFound('Empty Page')
#
#         context = {
#             'page_orders': page_orders
#         }
#
#         return render(request, 'user_center_order.html', context)


# <li class="col01">{{ order.create_time.strftime('%Y-%m-%d %H:%M:%S') }}</li>