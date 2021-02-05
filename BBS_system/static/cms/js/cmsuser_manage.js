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
        var dialog = $("#banner-dialog");
        var usernameInput = $("input[name='username']");
        var passwordInput = $("input[name='password']");
        var password2Input = $("input[name='password2']");
        var emailInput = $("input[name='email']");
        var roleInput = $("input[name='role']");


        var username = usernameInput.val();
        var password = passwordInput.val();
        var password2 = password2Input.val();
        var email = emailInput.val();
        var role = roleInput.val();
        var cms_userId = self.attr("data-id");

        if(!username || !password || !password2 || !email || !role){
            lgalert.alertInfoToast('请输入完整的用户信息！');
            return;
        }

        // form 发送 <form action="提交的地址" method="post">
        lgajax.post({
            "url": '/cms/add_cms_user/',
            'data':{
                'username':username,
                'password': password,
                'password2': password2,
                'email':email,
                'role': role,
                'cms_user_id': cms_userId
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
        var role_id = tr.attr('data-name');
        var cms_user_id = tr.attr("data-id");

        lgalert.alertOneInput({
            'text': '1访问者 2运营人员 3管理员 4开发者',
            'placeholder':role_id,
            'confirmCallback': function (inputValue) {
                lgajax.post({
                    'url': '/cms/update_cms_user_role/',
                    'data': {
                        'cms_user_id': cms_user_id,
                        'role_id': inputValue
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
    $(".delete-board-btn").click(function (event) {
        var self = $(this);
        var tr = self.parent().parent();
        var cms_user_id = tr.attr('data-id');
        lgalert.alertConfirm({
            "msg":"您确定要删除这个用户吗？",
            'confirmCallback': function () {
                lgajax.post({
                    'url': '/cms/delete_cms_user/',
                    'data':{
                        // form  input name value
                        'cms_user_id': cms_user_id
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