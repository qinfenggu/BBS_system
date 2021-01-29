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
    $(".delete-comment-btn").click(function (event) {
        var self = $(this);
        var tr = self.parent().parent();
        var comment_id = tr.attr('data-id');
        lgalert.alertConfirm({
            "msg":"您确定要删除这个评论吗？",
            'confirmCallback': function () {
                lgajax.post({
                    'url': '/cms/delete_comment/',
                    'data':{
                        // form  input name value
                        'comment_id': comment_id
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