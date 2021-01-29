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

$(function (){
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
        var sms_captchaE = $("input[name='sms_captcha']");
        var newpwdE = $("input[name='newpwd']");
        var newpwd2E = $("input[name='newpwd2']");

        var telephone = telephoneE.val();
        var sms_captcha = sms_captchaE.val();
        var newpwd = newpwdE.val();
        var newpwd2 = newpwd2E.val();

        lgajax.post({
            'url': '/FindPassword/',
            'data': {
                'telephone': telephone,
                'sms_captcha': sms_captcha,
                'newpwd': newpwd,
                'newpwd2': newpwd2
            },
            'success': function (data) {
                if(data['code'] == 200){
                    telephoneE.val("");
                    sms_captchaE.val("");
                    newpwdE.val("");
                    newpwd2E.val("");
                    lgalert.alertSuccessToast('操作成功！');
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