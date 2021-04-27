from . import api
from lghome.utils.commons import login_required
from flask import g, request, jsonify, session
from lghome.response_code import RET
from lghome.libs.image_storage import storage
import logging
from lghome.models import Area, House, Facility, HouseImage, User, Order
from lghome import db, redis_store
from lghome import constants
from datetime import datetime
import json


# 当在首页、发布房源、搜索页码点击 '区域选择框'时就会触发这个视图。
@api.route("/areas")
def get_area_info():
    """获取城区信息"""

    # 用redis中读取数据
    try:
        response_json = redis_store.get("area_info")
    except Exception as e:
        logging.error(e)
    else:
        # redis有缓存数据
        if response_json is not None:
            # 字节直接使用json.loads
            response_json = json.loads(response_json)
            logging.info('redis cache')
            return jsonify(errno=RET.OK, errmsg='OK', data=response_json['data'])

    # 查询数据库,读取城区信息
    try:
        area_li = Area.query.all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    area_dict_li = []
    # area_li查询出来的它是一个多条数据对象。循环就可得一条数据
    for area in area_li:
        area_dict_li.append(area.to_dict())  # area_dict_li就会变成[{}, {}, {}, ...]

    # 将数据转成json字符串。转换字典格式: dict(key=value)
    response_dict = dict(data=area_dict_li)  # 变成{ data：[{}, {}, {}, ....] }
    response_json = json.dumps(response_dict)  # 变成'{ data：[{}, {}, {}, ....] }'这种json类型即字符串

    try:
        # 设置过期时间。这样子就可以让过期后重新查询mysql数据库，可以及时更新数据
        redis_store.setex("area_info", constants.AREA_INFO_REDIS_CACHE_EXPIRES, response_json)
    except Exception as e:
        logging.error(e)

    # return response_json, 200, {"Content-Type": "application/json"}
    return jsonify(errno=RET.OK, errmsg='OK', data=area_dict_li)


@api.route("/houses/info", methods=["POST"])
@login_required
def save_house_info():
    """
    保存房屋的基本信息
    :return: 保存失败或者保存成功
    {
    "title":"1",
    "price":"1",
    "area_id":"8",
    "address":"1",
    "room_count":"1",
    "acreage":"1",
    "unit":"1",
    "capacity":"1",
    "beds":"1",
    "deposit":"1",
    "min_days":"1",
    "max_days":"1",
    "facility":["2","4"]
    }
    """
    # 发布房源的用户
    user_id = g.user_id

    house_data = request.get_json()
    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数 2
    max_days = house_data.get("max_days")  # 最大入住天数 1
    facility = house_data.get("facility")  # 设备信息

    # 校验参数
    if not all([title, price, area_id, address, room_count, acreage, unit]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 判断价格是否正确
    try:
        # 房价、押金必须是整数。保存到数据库里面是分的
        price = int(float(price)*100)    # 分
        deposit = int(float(deposit)*100)    # 分
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 判断区域ID
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='数据库异常')

    if area is None:
        return jsonify(errno=RET.PARAMERR, errmsg='城区信息有误')

    # 保存房屋信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )
    # 设施信息
    facility_ids = house_data.get("facility")

    # 判断传过的设备信息是否在数据库里面存在的
    if facility_ids:
        # 在facility这个表里面是不存在24的id的。如果前端传的数据是这种:["23", "24"]
        try:
            # 如果["23", "24"]这种的话，因为使用了filter这个查询语句，必然会报错
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库异常')

        if facilities:
            # 表示有合法的设备。多对多单个表添加数据
            house.facilities = facilities
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK', data={"house_id": house.id})


# 是js那边进行了处理，当/houses/info进行post请求操作很顺利成功后，就会显示上传图片页面。
@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """
    保存房屋的图片
    :param:house_id 房屋的ID   house_image 房屋的图片
    :return: image_url 房屋图片地址
    """
    # 接收参数。因为是
    image_file = request.files.get("house_image")
    house_id = request.form.get("house_id")

    # 校验
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    # 图片上传到七牛云
    image_data = image_file.read()
    try:
        #  filename是hash对图片加密得到的字符
        filename = storage(image_data)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='保存图片失败')

    # 保存图片信息到数据库(图片的名字)
    house_image = HouseImage(house_id=house_id, url=filename)
    db.session.add(house_image)

    # 处理房屋的主图
    if not house.index_image_url:
        # 这个是修改数据
        house.index_image_url = filename
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 域名+hash加密图片名字得到的字符
    image_url = constants.QINIU_URL_DOMAIN + filename
    return jsonify(errno=RET.OK, errmsg='OK', data={"image_url": image_url})


@api.route("/user/houses", methods=["GET"])
@login_required
def get_user_houses():
    """
    获取用户发布的房源
    :return: 发布的房源信息
    """
    # 获取当前的用户
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
        # 这个houses就相当于这个用户所属的所有houses数据
        houses = user.houses
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取数据失败')

    # 转成字典存放到列表中。
    houses_list = []
    if houses:
        # 这个houses
        for house in houses:
            houses_list.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_list})


@api.route("/houses/index", methods=["GET"])
def get_house_index():
    """
    获取首页房屋信息
    :return: 排序后的房屋信息
    """

    # 先查询缓存数据
    try:
        result = redis_store.get("home_page_data")
    except Exception as e:
        logging.error(e)
        result = None

    if result:
        return result.decode(), 200, {"Content-Type": "application/json"}
    else:
        try:
            # 查询数据库,房屋订单最多的5条
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_NUMS).all()
        except Exception as e:
            return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")

        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="查询没有数据")

        houses_list = []
        for house in houses:
            houses_list.append(house.to_basic_dict())

        house_dict = dict(errno=RET.OK, errmsg="OK", data=houses_list)
        json_houses = json.dumps(house_dict)

        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            logging.error(e)

        return json_houses, 200, {"Content-Type": "application/json"}
        # return jsonify(errno=RET.OK, errmsg="OK", data=houses_list)


@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """
    获取房屋详情
    :param house_id: 房屋的ID
    :return: 房屋的详细信息
    """
    # 当前用户
    # 不可以使用g对象原因：获取房屋详情页一定要登录才可以访问，我不登录页可以访问。session.get("user_id")可能会获取不到会报错。
    # 所以给一个默认值-1，因为-1永远不会有这个用户id
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 先从缓存中查询数据。看是否有这个房屋信息
    try:
        result = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        logging.error(e)
        result = None

    if result:
        # 首先不可以继续使用jsonify(errno=RET.OK, errmsg='OK', data={"house": house_data, "user_id": user_id})原因，
        # result.decode已经是json了，它不是字典了所以不可以继续使用jsonify。其实result.decode这个是一个json数据，
        # 需要一个key所以{"house": %s, "user_id": %s}}。因为return所以需要：200, {"Content-Type": "application/json"}
        return '{"errno":%s, "errmsg":"OK", "data":{"house": %s, "user_id": %s}}' % (RET.OK, result.decode(), user_id), 200, {"Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    house_data = house.to_full_dict()

    # 把该房屋信息保存到redis里面的。把房屋信息需要从字典变成json的原因是，setex是一个字符串的用法
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE, json_house)
    except Exception as e:
        logging.error(e)
    print(house_data['img_urls'])
    return jsonify(errno=RET.OK, errmsg='OK', data={"house": house_data, "user_id": user_id})


# 当首页或者在搜索页码选择完城区、入住时间、离开时间后点击'搜索'就会触发:
# http://127.0.0.1:5000/api/v1.0/houses?aid=城区id&sd=入住时间&ed=离开时间&sk=默认排序是按new&p=页码。
@api.route("/houses", methods=["GET"])
def get_house_list():
    """
    房屋的搜索页面
    :param: aid   区域的id   sd    开始时间 ed    结束时间 sk    排序  p  页码
    :return: 符合条件的房屋
    """
    # 接收参数
    start_date = request.args.get('sd')
    end_date = request.args.get('ed')
    area_id = request.args.get('aid')
    sort_key = request.args.get('sk')
    page = request.args.get('p')

    # 校验参数。入住时间和离开时间获取到的是字符串。需要转换成时间类型按格式:2020-12-04
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        if start_date and end_date:
            # 如果离开时间不是大于或等于入住时间，就断言抛出异常
            assert start_date <= end_date
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='日期参数有误')

    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='区域参数有误')

    try:
        # 如果page参数无法转换成整形，就默认是1
        page = int(page)
    except Exception as e:
        logging.error(e)
        page = 1

    # 查询缓存数据
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        logging.error(e)
    else:
        if resp_json:
            # resp_json.decode()就是一个json类型，不用loads转换成字典了
            return resp_json.decode(), 200, {"Content-Type": "application/json"}

    # 查询数据库。如果这里不定义conflict_orders为None，下面万一一条冲突订单都没有。这个conflict_orders变量名如果在后面用它，
    # 就会报出conflict_orders是未定义的变量名的错误
    conflict_orders = None
    # 过滤条件
    filter_params = []

    try:
        """
        这里是按一个房源只出租一个房屋算的。
        如果只选择入住时间，离开时间不选，默认是无穷大时间。那么想预定这个房间，入住时间必须得大于上一个订单退房即离开时间才可以预定
        如果只选择离开时间，入住时间默认是无穷小时间，那么想预定这个房间，离开时间必须得小于上一个订单入住时间才可以预定
        如果都有选择入住和离开时间，那么想预定，入住和离开时间必须同时小于上一个订单入住时间或同时大于上一个订单离开时间才可预定
        """
        if start_date and end_date:
            # 查询冲突的订单
            conflict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    # print(conflict_orders)
    if conflict_orders:
        # 从订单中获取冲突的房屋ID
        conflict_house_id = [order.house_id for order in conflict_orders]

        if conflict_house_id:
            # 使用解包知识
            filter_params.append(House.id.notin_(conflict_house_id))

    if area_id:
        # 查询的条件
        filter_params.append(House.area_id == area_id)

    # 排序
    if sort_key == "booking":
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())  # 入住最多即订单数量
    elif sort_key == "price-inc":
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == "price-des":
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())  # 默认按最新发布房源时间

    # 处理分页。error_out自动输出错误。page当前页码。per_page每页显示多少条数据即当前页显示多少条
    page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_NUMS, error_out=False)

    # 总页数
    total_page = page_obj.pages

    # 获取当前页所要显示的那几条数据
    house_li = page_obj.items

    houses = []
    # 循环可以得出具体的一条数据。一条即对应数据库里面一行的数据。
    for house in house_li:
        houses.append(house.to_basic_dict())

    # 这个是定义了resp_dict的字典。是为了字典——》变成json
    resp_dict = dict(errno=RET.OK, errmsg="OK", data={"total_page": total_page, "houses": houses})
    resp_json = json.dumps(resp_dict)

    # 将数据保存到redis中
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        # redis管道
        pipeline = redis_store.pipeline()

        pipeline.hset(redis_key, page, resp_json)
        pipeline.expire(redis_key, constants.HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES)
        pipeline.execute()

    except Exception as e:
        logging.error(e)

    return jsonify(errno=RET.OK, errmsg="OK", data={"total_page": total_page, "houses": houses})


"""
预定界面是，房源详情页面点击即可预定触发的，无序我这边弄接口，而且预定界面里面的房源信息和金额这些信息都是前端那边弄，
对接的是booking.html。无须弄接口提供信息
"""



