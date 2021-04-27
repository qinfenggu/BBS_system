# @ Time    : 2021/3/22 21:17
# @ Author  : JuRan
from collections import OrderedDict
from goods.models import GoodsCategory, GoodsChannel


def get_categories():
    # 查询并展示商品分类
    categories = OrderedDict()
    # GoodsChannel是商品频道，group_id频道组id。查询所有的商品频道，并以组和组内sequence排序。每一组里面也是有sequence字段序号标记的
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    # print(type(categories))

    for channel in channels:
        # 37个频道,11个组
        # print(type(channel))
        group_id = channel.group_id
        # 如果存在有即频道组（id）没有写，就给这个频道组定义框架
        if group_id not in categories:
            categories[group_id] = {'channels': [], 'sub_cats': []}

        # 商品频道和商品频道组存在外键关系。category就是商品频道表以商品频道组id为外键的字段
        cat1 = channel.category

        categories[group_id]['channels'].append(
            {
                'id': cat1.id,
                'name': cat1.name,
                'url': channel.url
            }
        )
        # 查询二级和三级类别
        # 查询二级  parent_id = cat1.id
        # for cat2 in cat1.subs.all():
        for cat2 in GoodsCategory.objects.filter(parent_id=cat1.id).all():
            cat2.sub_cats = []
            categories[group_id]['sub_cats'].append(
                {
                    'id': cat2.id,
                    'name': cat2.name,
                    'sub_cats': cat2.sub_cats
                }
            )
            # for cat3 in cat2.subs.all()
            for cat3 in GoodsCategory.objects.filter(parent_id=cat2.id).all():
                cat2.sub_cats.append({
                    'id': cat3.id,
                    'name': cat3.name
                })

    return categories


"""
     {
            "1 group_id即频道组的id":
            {
                "channels":
                [
                    {"这个频道组里面频道即一类级别id":1, "name":"频道", "url":"http://shouji.jd.com/"},
                     ....
                ],

                "sub_cats":
                [
                    {
                        "这个频道组里面频道即二类级别id":38, 
                        "name":"二类级别商品名", 
                        "sub_cats":[
                                    {"这个二类级别里面的三类级别id":115, "name":"三类级别商品名"},
                                     ....
                                   ]
                    },
                    .....
                ]
            },
            ....

        }
"""