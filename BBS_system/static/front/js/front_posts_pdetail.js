
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

$(function(){
    var ue = UE.getEditor("editor", {
        "serverUrl": "/ueditor/upload",
       toolbars: [
        ['fullscreen', 'source', 'undo', 'redo'],
        ['bold', 'italic', 'underline', 'fontborder', 'strikethrough', 'superscript', 'subscript', 'removeformat', 'formatmatch',
         'autotypeset', 'blockquote', 'pasteplain', '|', 'forecolor', 'backcolor', 'insertorderedlist', 'insertunorderedlist',
         'selectall', 'cleardoc']
]
    });
    window.ue = ue;
})

$(function () {
    $("#comment-btn").click(function (event) {
        event.preventDefault();

//        var content = $("#comment").val();
        var content = window.ue.getContent();
        var posts_id = $("#post-content").attr("data-id");
        lgajax.post({
            'url': '/add_comment/',
            'data':{
                'content': content,
                'posts_id': posts_id
            },
            'success': function (data) {
                if(data['code'] == 200){
                    window.location.reload();
                }else{
                    lgalert.alertInfo(data['message']);
                }
            }
        });
//        }
    });
});


$(function () {
    $(".btn-xs").click(function () {
        var self = $(this);
        // var tr = self.parent().parent();
        // var comment_id = tr.attr("data-id");
        // var comment_id = 3;
         var comment_id = $("#comment-content").attr("data-id");
        lgalert.alertConfirm({
            "msg":"您确定要删除该评论吗？",
            'confirmCallback': function () {
                lgajax.post({
                    'url': '/delete_comment/',
                    'data':{
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