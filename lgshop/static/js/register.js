// es6
let vm = new Vue({
    el: "#app",
    // 修改Vue读取变量的语法  {{}}  [[]]
    delimiters: ['[[',']]'],
    data:{
        // v-model
        username: "",
        password: "",
        password2: "",
        mobile: "",
        allow: "",
        image_code_url: "",
        uuid: "",
        image_code: "",
        sms_code: "",
        sms_code_tip: "获取短信验证码",
        send_flag: false,

        // v-show
        error_name: false,
        error_password: false,
        error_password2: false,
        error_mobile: false,
        error_allow: false,
        error_image_code: false,
        error_sms_code: false,

        // error_message
        error_name_message: "",
        error_mobile_message: "",
        error_image_code_message: "",
        error_sms_code_message: ""


    },
    // 页面加载完成后被调用
    mounted(){
        this.generate_image_code();
    },
    methods:{
        // check_username:function(){
        // }

        check_sms_code(){
            if(this.sms_code.length != 6){
                this.error_sms_code_message = '请填写短信验证码'
                this.error_sms_code = true
            }else{
                this.error_sms_code = false
            }
        },

        send_sms_code(){
             // 作用：如果send_flag为true就不给你发短信了，已经发过了！如果是false就给你发短信
            if (this.send_flag == true){
                return;
            }

            this.send_flag = true
            // 校验数据  手机号  图像验证码
            this.check_mobile();
            this.check_image_code();
            if (this.error_mobile == true || this.error_image_code == true){
                return;
            }
           // sms_codes/1xxxx/?image_code='xxx'&uuid='xxx'
           // sms_codes/18646175116/?image_code=qwqq&uuid=23b4db44-2048-4534-8ecc-a3d5d9b09735
           let url = '/sms_codes/' + this.mobile + '/?image_code=' + this.image_code + '&uuid=' + this.uuid
           axios.get(url, {
                responseType: 'json'
           })
           .then(response=>{
                let num = 60
                if(response.data.code == '0'){
                    // 定时器
                    let t = setInterval(()=>{
                        if (num == 1){
                            // 定时器停止
                            clearInterval(t)
                            this.sms_code_tip = '获取短信验证码'
                            this.generate_image_code();  //重新生成图像验证码
                            this.send_flag = false
                        }else{
                            num -= 1
                            this.sms_code_tip = num + '秒'
                        }
                    },1000)

                }else{
                    if (response.data.code == '4001'){
                        // 图形验证码输入有误
                        this.error_sms_code_message = response.data.errmsg
                        this.error_image_code = true
                    }
                    this.send_flag = false
                }
           })
           .catch(error => {
                console.log(error.response)
                this.send_flag = false
            })

        },

        generate_image_code(){
            this.uuid = generateUUID()
            this.image_code_url = "/image_codes/" + this.uuid + "/"
        },
        check_username(){
            let re = /^[a-zA-Z0-9_-]{5,20}$/;
            if(re.test(this.username)){
                // 匹配成功 错误提示信息 不展示
                this.error_name = false
            }else{
                this.error_name = true
                this.error_name_message = '请输入5-20个字符的用户名'
            }

            if(this.error_name == false){
                // http://127.0.0.1:8000/users/usernames/ xxxx / count
                let url = '/users/usernames/' + this.username + '/count'

                axios.get(url, {
                    responseType:'json'
                })
                // 请求成功的处理  function(response){}
                .then(response=>{
                    if (response.data.count == 1){
                        // 用户名已经存在
                        this.error_name_message = '用户名已经存在'
                        this.error_name = true
                    }else{
                        this.error_name = false
                    }
                })
                // 请求失败
                .catch(error => {
                    console.log(error.response)
                })
            }
        },
        check_password(){
            let re = /^[a-zA-Z0-9]{8,20}$/;
            if (re.test(this.password)){
                this.error_password = false
            }else{
                this.error_password = true
            }
        },
        check_password2(){
            if(this.password != this.password2){
                this.error_password2 = true
            }else{
                this.error_password2 = false
            }
        },
        check_mobile(){
            let re = /^1[3456789]\d{9}$/;
            if (re.test(this.mobile)){
                this.error_mobile = false
            }else{
                this.error_mobile = true
                this.error_mobile_message = "请输入正确的手机号"
            }
            if(this.error_mobile == false){
                // http://127.0.0.1:8000/users/usernames/ xxxx / count
                let url = '/users/mobile/' + this.mobile +'/'
                axios.get(url, {
                    responseType:'json'
                })
                // 请求成功的处理  function(response){}
                .then(response=>{
                    if (response.data.count == 1){
                        // 用户名已经存在
                        this.error_mobile_message = '手机号已经注册过'
                        this.error_mobile = true
                    }else{
                        this.error_mobile = false
                    }
                })
                // 请求失败
                .catch(error => {
                    console.log(error.response)
                })
            }
        },
        check_allow(){

            if(!this.allow){
                this.error_allow = true
            }else{
                this.error_allow = false
            }
        },

        check_image_code(){
            if(this.image_code.length != 4){
                this.error_image_code_message = '图形验证码长度为4'
                this.error_image_code = true
            }else{
                this.error_image_code = false
            }
        },

        // 表单提交
        on_submit(){
            if(this.error_name == true || this.error_password || this.error_password2 || this.error_mobile == true || this.error_allow == true){
                // 禁止表单提交
                   window.event.returnValue=false
            }
        }
    }
})