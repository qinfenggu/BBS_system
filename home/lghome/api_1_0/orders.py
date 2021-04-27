# @ Time    : 2020/12/8 20:56
# @ Author  : JuRan

from . import api
from lghome.utils.commons import login_required
from flask import g, request, jsonify
from lghome.response_code import RET
import logging
from lghome.models import Area, House, Order
from lghome import db
from datetime import datetime
from lghome import redis_store


@api.route("/orders", methods=["POST"])
@login_required
def save_order():
    """
    保存订单
    :param: start_date  end_date house_id
    :return: 保存订单的状态
    """
    # 接收参数
    user_id = g.user_id

    order_data = request.get_json()
    if not order_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    start_date = order_data.get('start_date')
    end_date = order_data.get('end_date')
    house_id = order_data.get('house_id')

    # 校验参数
    if not all([start_date, end_date, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 接收过来的时间是一个str类型。需要转成时间类型，因为数据库中保存
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        assert start_date <= end_date
        # 预定的天数。加1原因：如果入住时间和离开时间都是选择当天，就会得到是0，+1就是表示住一天。比如2021.4.25-2021.4.26这算两天，
        # 本项目就是运用这个思想。求这个天数原因：在显示页面时，有一个地方是要显示这个订单住几晚
        days = (end_date - start_date).days + 1

    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期格式错误")

    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取房屋信息失败")

    # 因为使用get，查询不出来值是None，不会报错。所以要判断是否有值
    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 预定的房屋是否是房东自己。虽然前端页面如果是房东自己看自己发布房源，是无法展示出'预定'提交按钮。但是前端的东西不可信，
    # 对程序员来说有一百万种方法可以绕过这个坎
    if user_id == house.user_id:
        # 说明是房东自己
        return jsonify(errno=RET.ROLEERR, errmsg="不能预定自己的房间")

    # 查询这个房间的时间冲突订单数量
    try:
        count = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date, Order.house_id == house_id).count()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="订单数据有误")

    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg="房屋已经被预定")

    # 订单总金额
    amount = days * house.price

    # 保存订单数据
    order = Order(
        user_id=user_id,
        house_id=house_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount
    )

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存订单失败")

    # js那边不需要给它传什么参数
    return jsonify(errno=RET.OK, errmsg="OK")


# 在个人中心那里，点击'我的订单'：http://127.0.0.1:5000/api/v1.0/user/orders?role=custom。会发送这个请求，表示是以房客身份访问
# 在个人中心那里，点击'我的订单'：http://127.0.0.1:5000/api/v1.0/user/orders?role=landlord。会发送这个请求，表示是以房东身份访问
@api.route("/user/orders", methods=["GET"])
@login_required
def get_user_orders():
    """
    查询用户的订单信息：不同角色，显示的信息不一样
    :param: role 角色   custom  landlord
    :return: 订单的信息
    """
    user_id = g.user_id

    role = request.args.get("role", "")

    # print(role)

    try:
        if role == "landlord":
            # 房东
            # 先查询属于自己的房子。然后根据房间id去匹配订单表里面所属这个房东id的订单
            houses = House.query.filter(House.user_id == user_id).all()
            houses_id = [house.id for house in houses]

            # 根据房子的ID 查询预定了自己房子的订单
            orders = Order.query.filter(Order.house_id.in_(houses_id)).order_by(Order.create_time.desc()).all()

        else:
            # 客户的身份。根据自己的用户id，是订单表里面匹配所属这个用户id订单。
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询订单失败")

    orders_dict_list = []
    if orders:
        for order in orders:
            orders_dict_list.append(order.to_dict())
    # orders_dict_list：[{订单1信息}, {订单2信息}]
    return jsonify(errno=RET.OK, errmsg="OK", data={"orders": orders_dict_list})


# 接单还是拒单，其实就是把订单表里面的状态字段修改一下。如果是拒单，顺便在表字段里面的commont添加上拒单原因。
# 如果是接单，交易完成看样子在这个commont这个字段添加评论
@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_required
def accept_reject_order(order_id):
    """
    房东接单 拒单
    :param order_id: 订单ID
    :return: json
    """
    # 如果没有这个user_id。那我知道你这个oder_id此不是可以修改任何订单
    user_id = g.user_id

    # 接收参数
    request_data = request.get_json()
    if not request_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 拒绝还是接单
    action = request_data.get('action')

    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        # 根据订单号,查询数据库是否存在order_id并且状态是WAIT_ACCEPT的订单
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        # 因为在huose表里面有写 orders = db.relationship("Order", backref="house")  # 房屋的订单。order.house就是这个订单所属的房屋的一行数据
        house = order.house
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单数据')

    # 要确保这个订单所属的房东di==当前登录用户id。保证房东只能修改自己的房子的订单
    """这个视图主要有掌握的开发思维就是这里：要确保操作当前订单所属的房屋的所属房东 == 当前登录的用户。不然订单任何人都可以操作此不是乱套了"""
    if house.user_id != user_id:  # house.user_id是该订单所属房屋的房东id ； user_id当前登录用户的id
        return jsonify(errno=RET.REQERRE, errmsg='操作无效')

    if action == "accept":
        # 接单
        order.status = "WAIT_PAYMENT"
    elif action == "reject":
        # 拒单
        order.status = "REJECTED"
        # 如果是拒单，request_data里面还会传一个拒单原因
        reason = request_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
        order.comment = reason

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')

    return jsonify(errno=RET.OK, errmsg='OK')


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    """
    保存订单评论信息
    :param order_id: 订单ID
    :return: json
    """
    # 接收参数
    user_id = g.user_id
    request_data = request.get_json()
    comment = request_data.get("comment")

    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        # 确保这个订单存在并且状态已经是"WAIT_COMMENT",还是这个订单所属的用户id==你当前登录用户的id，不能谁都可以操作这个订单
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_COMMENT", Order.user_id == user_id).first()
        # 因为在house模型类里面：  orders = db.relationship("Order", backref="house")。所以order.house就是相当于这个订单所属的房屋一行数据
        house = order.house
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单数据')

    if not order:
        return jsonify(errno=RET.DBERR, errmsg='操作无效')

    try:
        order.status = "COMPLETE"
        order.comment = comment

        # 将房屋订单加1
        house.order_count += 1
        db.session.add(house)
        db.session.add(order)

        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')

    # 删除缓存
    try:
        # 第一次查看这个房屋详情信息时候，会把这个信息保存到redis里面的。以后有一段时间都是从redis里面取。而你房屋的详情页面里面有评论，
        # 现在数据更新了，肯定需要把redis里面的缓存给删除掉。
        redis_store.delete("house_info_%s" % order.house_id)
    except Exception as e:
        logging.error(e)

    return jsonify(errno=RET.OK, errmsg='OK')























