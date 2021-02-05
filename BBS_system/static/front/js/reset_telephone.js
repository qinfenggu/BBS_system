var param = {
    setParam: function (href,key,value) {
        // 重新加载整个页面
        var isReplaced = false;
        var urlArray = href.split('?');
        if(urlArray.length > 1){
            var queryArray = urlArray[1].split('&');
            for(var i=0; i < queryArray.length; i++){
                var paramsArray = queryArray[i].split('=');
                if(paramsArray[0] == key){
                    paramsArray[1] = value;
                    queryArray[i] = paramsArray.join('=');
                    isReplaced = true;
                    break;
                }
            }

            if(!isReplaced){
                var params = {};
                params[key] = value;
                if(urlArray.length > 1){
                    href = href + '&' + $.param(params);
                }else{
                    href = href + '?' + $.param(params);
                }
            }else{
                var params = queryArray.join('&');
                urlArray[1] = params;
                href = urlArray.join('?');
            }
        }else{
            var param = {};
            param[key] = value;
            if(urlArray.length > 1){
                href = href + '&' + $.param(param);
            }else{
                href = href + '?' + $.param(param);
            }
        }
        return href;
    }
};


$(function(){
    //  http://127.0.0.1:5000/captcha/?x=0.2
    $('#captcha-img').click(function (event) {
        var self = $(this);
        var src = self.attr('src');
        var newsrc = param.setParam(src,'xx',Math.random());
        self.attr('src',newsrc);
    });
});


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
    $("#sms-captcha-btn").click(function (event) {
        event.preventDefault();
        var self = $(this);
       var telephone = $("input[name='telephone']").val();
       if(!(/^1[345879]\d{9}$/.test(telephone))){

           lgalert.alertInfo('请输入正确的手机号码！');
           return;
       }
       var timestamp = (new Date).getTime();

       var sign = md5(timestamp+telephone+"q3423805gdflvbdfvhsdoa`#$%");
       lgajax.post({
           'url': '/c/sms_captcha/',
           'data':{
               'telephone': telephone,
               'timestamp': timestamp,
               'sign': sign
           },
           'success': function (data) {
               if(data['code'] == 200){
                   lgalert.alertSuccessToast('短信验证码发送成功！');
                   self.attr("disabled",'disabled');
                   var timeCount = 60;
                   var timer = setInterval(function () {
                       timeCount--;
                       self.text(timeCount);
                       if(timeCount <= 0){
                           self.removeAttr('disabled');
                           clearInterval(timer);
                           self.text('发送验证码');
                       }
                   },1000);
               }else{
                   lgalert.alertInfoToast(data['message']);
               }
           }
       });
   });
});

$(function () {
    $("#submit").click(function (event) {
        event.preventDefault();
        var telephoneE = $("input[name='telephone']");
        var captchaE = $("input[name='sms_captcha']");
        var graph_captcha_input = $("input[name='graph_captcha']");

        var telephone = telephoneE.val();
        var captcha = captchaE.val();
        var graph_captcha = graph_captcha_input.val();

        lgajax.post({
            'url': '/FrontResetTelephone/',
            'data': {
                'telephone': telephone,
                'captcha': captcha,
                'graph_captcha': graph_captcha
            },
            'success': function (data) {
                if(data['code'] == 200){
                    telephoneE.val("");
                    captchaE.val("");
                    graph_captcha_input.val("");
                    lgalert.alertSuccessToast('恭喜！手机号更换成功！');
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