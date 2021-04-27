from . import api
from lghome.utils.commons import login_required
from flask import g, request, jsonify
from lghome.response_code import RET
import logging
from lghome.models import Order
from lghome import db
from alipay import AliPay
import os


@api.route("/orders/<int:order_id>/payment", methods=["POST"])
@login_required
def order_pay(order_id):
    """
    发起支付宝支付
    :param order_id: 订单ID
    :return:
    """
    user_id = g.user_id
    try:
        # 查询属于这个order_id并且状态是"WAIT_PAYMENT"，这个没有问题吧，因为虽然你根据order_id可以查询出订单，
        # 但是万一这个订单状态不是"WAIT_PAYMNT"。然后就是Order.user_id == user_id原因：要确保当前登录用户==这个订单所属用户。
        # 不然谁的用户都可以操作这个订单，此不是乱套了
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_PAYMENT", Order.user_id == user_id).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if order is None:
        return jsonify(errno=RET.NODATA, errmsg='订单数据有误')
    # os.path.dirname(__file__)获取这个pay.py的父文件夹绝对路径
    app_private_key_string = open(os.path.join(os.path.dirname(__file__), r"keys\app_private_key.pem")).read()
    alipay_public_key_string = open(os.path.join(os.path.dirname(__file__), r"keys\alipay_public_key.pem")).read()

    alipay = AliPay(
        appid="2021000117645677",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=False,  # 默认False
    )

    # https://openapi.alipaydev.com/gateway.do
    # 电脑网站支付，需要跳转到 https://openapi.alipay.com/gateway.do? + order_string
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order.id,    # 订单编号
        total_amount=order.amount/100,      # 总金额。因为数据库里面存的是分。需要除以100
        subject='爱家 %s' % order.id,           # 订单的标题
        return_url="http://127.0.0.1:5000/payComplete.html",  # 支付成功了要跳到哪里的地址.返回的连接地址即
        notify_url=None  # 可选, 不填则使用默认notify url
    )
    # 这个跳转到支付宝支付链接l
    pay_url = "https://openapi.alipaydev.com/gateway.do?" + order_string

    return jsonify(errno=RET.OK, errmsg='OK', data={"pay_url": pay_url})


@api.route("/order/payment", methods=["PUT"])
def save_order_payment_result():
    """
    保存订单结果
    :return: json
    """
    data = request.form.to_dict()
    # sign 不能参与签名验证
    signature = data.pop("sign")

    app_private_key_string = open(os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem")).read()
    alipay_public_key_string = open(os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem")).read()

    alipay = AliPay(
        appid="2021000117645677",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=False,  # 默认False
    )

    success = alipay.verify(data, signature)
    if success:
        order_id = data.get('out_trade_no')
        trade_no = data.get('trade_no')     # 支付宝的交易号

        try:
            # 改变订单状态和添加支付宝的交易号
            Order.query.filter(Order.id == order_id).update({"status": "WAIT_COMMENT", "trade_no": trade_no})
            db.session.commit()
        except Exception as e:
            logging.error(e)
            db.session.rollback()

    return jsonify(errno=RET.OK, errmsg='OK')