
$(function () {
    $("#submit").click(function (event) {
        // event.preventDefault
        // 是阻止按钮默认的提交表单的事件
        event.preventDefault();

        var oldpwdE = $("input[name=oldpwd]");
        var newpwdE = $("input[name=newpwd]");
        var newpwd2E = $("input[name=newpwd2]");

        var oldpwd = oldpwdE.val();
        var newpwd = newpwdE.val();
        var newpwd2 = newpwd2E.val();

        // 1. 要在模版的meta标签中渲染一个csrf-token
        // 2. 在ajax请求的头部中设置X-CSRFtoken
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
//                            var csrftoken = $('input[name=csrf-token]').attr('value');
                            xhr.setRequestHeader("X-CSRFToken", csrftoken)
                        }
                    }
                });
            }
        };

        // 表单提交 方法  post 提交
        // 表单发送的地址
        // data 数据
        // success
        // fail
        lgajax.post({
            'url': '/FontResetPwd/',
            'data': {
                'oldpwd': oldpwd,
                'newpwd': newpwd,
                'newpwd2': newpwd2
            },
            // 成功表单验证通过
            'success': function (data) {
                // console.log(data);
                if(data['code'] == 200){
                    lgalert.alertSuccess('密码修改成功')
                    // 下面三个oldpwd.val("")这样子写的原因：如果修改密码成功了，那边旧密码，新密码，确认新密码
                    // 这三个input标签的value就变成空，好看一点。别让你刚刚输入的数字还继续在显示在那里
                    oldpwd.val("")
                    newpwd.val("")
                    newpwd2.val("")
                }else{
                    var message = data['message']
                    lgalert.alertInfo(message)
                }
            },
            // 表单验证不通过
            'fail': function (error) {
                // console.log(error);
                lgalert.alertNetworkError();
            }
        });
    });
});