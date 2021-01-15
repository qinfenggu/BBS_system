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
    $("#captcha-btn").click(function (event) {
        event.preventDefault();
        var email = $("input[name='email']").val();
        if(!email){
            lgalert.alertInfoToast('请输入邮箱');
            return;
        }
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
        lgajax.get({
            'url': '/cms/email_captcha/',
            'data': {
                'email': email
            },
            'success': function (data) {
                if(data['code'] == 200){
                    lgalert.alertSuccessToast('邮件发送成功！请注意查收！');
                }else{
                    lgalert.alertInfo(data['message']);
                }
            },
            'fail': function (error) {
                lgalert.alertNetworkError();
            }
        });
    });
});

$(function () {
    $("#submit").click(function (event) {
        event.preventDefault();
        var emailE = $("input[name='email']");
        var captchaE = $("input[name='captcha']");

        var email = emailE.val();
        var captcha = captchaE.val();

        lgajax.post({
            'url': '/cms/resetemail/',
            'data': {
                'email': email,
                'captcha': captcha
            },
            'success': function (data) {
                if(data['code'] == 200){
                    emailE.val("");
                    captchaE.val("");
                    lgalert.alertSuccessToast('恭喜！邮箱修改成功！');
                }else{
                    lgalert.alertInfo(data['message']);
                }
            },
            'fail': function (error) {
                lgalert.alertNetworkError();
            }
        });
    });
});