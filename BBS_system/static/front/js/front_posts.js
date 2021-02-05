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


    $("#submit-btn").click(function (event) {
        event.preventDefault();
        var titleInput = $('input[name="title"]');
        var boardSelect = $("select[name='board_id']");
        var contentText = $("textarea[name='content']");

        var title = titleInput.val();
        var board_id = boardSelect.val();
        var content = contentText.val();

        lgajax.post({
            'url': '/posts/',
            'data': {
                'title': title,
                'content':content,
                'board_id': board_id,
                // 'contentText': contentText
            },
            'success': function (data) {
                if(data['code'] == 200){
                    lgalert.alertConfirm({
                        'msg': '恭喜！帖子发表成功！',
                        'cancelText': '回到首页',
                        'confirmText': '再发一篇',
                        'cancelCallback': function () {
                            window.location = '/front_home_page/';
                        },
                        'confirmCallback': function () {
                            titleInput.val("");
                            boardSelect.val("");
                            contentText.val("");
                        }
                    });
                }else{
                    lgalert.alertInfo(data['message']);
                }
            }
        });
    });
});