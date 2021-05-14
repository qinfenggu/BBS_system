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
    $("#save-banner-btn").click(function (event) {
        event.preventDefault();
        var self = $(this);
        var tr = self.parent().parent();
        var dialog = $("#banner-dialog");
        var imageInput = $("input[name='image_url']");
        var front_user_id = tr.attr("data-id");
        var image_url = imageInput.val();


        if(!image_url){
            lgalert.alertInfoToast('请添加图片！');
            return;
        }

        // form 发送 <form action="提交的地址" method="post">
        lgajax.post({
            "url": '/add_head_portrait/',
            'data':{
                'image_url': image_url,
                'front_user_id': front_user_id
            },
            'success': function (data) {
                dialog.modal("hide");
                if(data['code'] == 200){
                    // 重新加载这个页面
                    window.location.reload();
                }else{
                    lgalert.alertInfo(data['message']);
                }
            },
            'fail': function () {
                lgalert.alertNetworkError();
            }
        });
    });
});



$(function () {
    $(".edit-board-btn").click(function () {
        var self = $(this);
        var tr = self.parent().parent();
        var old_value = tr.attr('data-name');
        var front_user_id = tr.attr("data-id");


        lgalert.alertOneInput({
            // 这text在弹出框是显示请输入
            'text': '',
            // 这个是输入框里面默认输入的内容
            'placeholder': old_value,
            // 这个是获取值
            'confirmCallback': function (inputValue) {
                lgajax.post({
                    'url': '/updata_front_username_signature/',
                    'data': {
                        'front_user_id': front_user_id,
                        'input_values': inputValue,
                        'old_value': old_value
                    },
                    'success': function (data) {
                        if(data['code'] == 200){
                            window.location.reload();
                        }else{
                            lgalert.alertInfo(data['message']);
                        }
                    }
                });
            }
        });
    });
});



$(function () {
    $(".edit-banner-btn").click(function (event) {
        var self = $(this);
        var dialog = $("#banner-dialog");
        dialog.modal("show");

        var tr = self.parent().parent();
        var name = tr.attr("data-name");
        var image_url = tr.attr("data-image");
        var link_url = tr.attr("data-link");
        var priority = tr.attr("data-priority");

        var nameInput = dialog.find("input[name='name']");
        var imageInput = dialog.find("input[name='image_url']");
        var linkInput = dialog.find("input[name='link_url']");
        var priorityInput = dialog.find("input[name='priority']");
        var saveBtn = dialog.find("#save-banner-btn");

        nameInput.val(name);
        imageInput.val(image_url);
        linkInput.val(link_url);
        priorityInput.val(priority);
        saveBtn.attr("data-type",'update');
        saveBtn.attr('data-id',tr.attr('data-id'));
    });
});






// 七牛云JS初始化
$(function () {
    lgqiniu.setUp({
        'domain': 'http://qsvqge52u.hd-bkt.clouddn.com/',
        'browse_btn': 'upload-btn',
        'uptoken_url': '/c/updata_token/',
        'success': function (up,file,info) {
            var imageInput = $("input[name='image_url']");
            imageInput.val(file.name);
        }
    });
});