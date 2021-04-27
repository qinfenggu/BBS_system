# @ Time    : 2021/3/22 21:51
# @ Author  : JuRan
from .models import GoodsCategory


def get_breadcrumb(category):
    """
    查询面包屑
    :param category: 类别对象
    :return:
    一级: 返回一级 breadcrumb = {'cat1': ''}
    二级: 返回二级 breadcrumb = {'cat1': '', 'cat2': ''}
    三级: 返回三级 breadcrumb = {'cat1': '', 'cat2': '', 'cat3': ''}
    """

    breadcrumb = {
        'cat1': '',
        'cat2': '',
        'cat3': ''
    }
    if category.parent == None:
        # 一级
        breadcrumb['cat1'] = category
    elif GoodsCategory.objects.filter(parent_id=category.id).count() == 0:
        # 三级
        cat2 = category.parent
        breadcrumb['cat1'] = cat2.parent
        breadcrumb['cat2'] = cat2
        breadcrumb['cat3'] = category
    else:
        # 二级
        breadcrumb['cat1'] = category.parent
        breadcrumb['cat2'] = category

    return breadcrumb