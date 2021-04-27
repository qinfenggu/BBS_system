from django.shortcuts import render
from django.views import View
from .models import ContentCategory, Content
from .utlis import get_categories


class IndexView(View):
    """首页广告"""

    def get(self, request):
        """提供首页页面"""
        # 查询三级分类页面三级类别的数据
        categories = get_categories()

        # 查询是所有的广告类别
        context_categories = ContentCategory.objects.all()
        contents = {}

        """
        {   
            # 在广告类别表里面有一个key字段，是可以区别广告类别的，当然也可以用广告类别id，听你
            "广告类别key":[
                            {
                                广告content1，是一个查询对象
                            },
                            {
                                广告content2，是一个查询对象
                            }
                            ....
                        ]，
            ....
        },
        """

        for context_category in context_categories:
            # 同一个广告类别里面的广告也是由sequence字段进行排序先后。category_id本身就有广告类别排序，哪个广告类别在前一点，哪个在后一点
            contents[context_category.key] = Content.objects.filter(category_id=context_category.id, status=True).all().order_by('sequence')

        context = {
            'categories': categories,
            'contents': contents       # 这个是{'key1'：[查询广告对象1，广告对象2，...], 'key2':[..] }
        }
        return render(request, 'index.html', context=context)