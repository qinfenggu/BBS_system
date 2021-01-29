var lgajax = {
    'get':function(args) {
        args['method'] = 'get';
        this.ajax(args);
    },
    'post':function(args) {
        args['method'] = 'post';
        this.ajax(args);
    },
    'ajax':function(args) {
        // 设置csrftoken
        this._ajaxSetup();
        $.ajax(args);
    },
    '_ajaxSetup': function() {
        $.ajaxSetup({
            'beforeSend':function(xhr,settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    var csrftoken = $('meta[name=csrf-token]').attr('content');
                    xhr.setRequestHeader("X-CSRFToken", csrftoken)
                }
            }
        });
    }
};

$(function () {
    $(".highlight-btn").click(function () {
        var self = $(this);
        var tr = self.parent().parent();
        var post_id = tr.attr("data-id");
        var highlight = parseInt(tr.attr("data-highlight"));
        var url = "";
        if(highlight){
            url = "/cms/unbecome_essence_posts/";
            lgalert.alertConfirm({
                "msg":"您确定要取消加精这篇帖子吗？",
                'confirmCallback': function () {
                    lgajax.post({
                        'url': url,
                        'data': {
                            'post_id': post_id
                        },
                        'success': function (data) {
                            if(data['code'] == 200){
                                lgalert.alertSuccessToast('操作成功！');
                                setTimeout(function () {
                                    window.location.reload();
                                },500);
                            }else{
                                zlalert.alertInfo(data['message']);
                            }
                        }
                    });
                }
            });
        }else {
            url = "/cms/become_essence_posts/";
            lgalert.alertConfirm({
                "msg":"您确定要加精这篇帖子吗？",
                'confirmCallback': function () {
                    lgajax.post({
                        'url': url,
                        'data': {
                            'post_id': post_id
                        },
                        'success': function (data) {
                            if(data['code'] == 200){
                                lgalert.alertSuccessToast('操作成功！');
                                setTimeout(function () {
                                    window.location.reload();
                                },500);
                            }else{
                                zlalert.alertInfo(data['message']);
                            }
                        }
                    });
                }
            });
        }
    });
});


$(function () {
    $(".btn-xs").click(function () {
        var self = $(this);
        var tr = self.parent().parent();
        var post_id = tr.attr("data-id");
        lgalert.alertConfirm({
            "msg":"您确定要删除这篇帖子吗？",
            'confirmCallback': function () {
                lgajax.post({
                    'url': '/cms/delete_essence_posts/',
                    'data':{
                        'post_id': post_id
                    },
                    'success': function (data) {
                        if(data['code'] == 200){
                            window.location.reload();
                        }else{
                            lgalert.alertInfo(data['message']);
                        }
                    }
                })
            }
        });


    });
});