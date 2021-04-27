OAuth 2.0认证流程：

```
QQ_CLIENT_ID = '101913612'   # 这是在QQ互联上创建应用后得到的appid和appkey
QQ_CLIENT_SECRET = '39eb6ac28cb343b3e5562ef1032b7cab'  # 和appkey
QQ_REDIRECT_URI = 'http://www.meiduo.site:8000/oauth_callback'  # 和
```


对于应用而言，需要进行两步： 

1. 获取Authorization Code； 
2. 通过Authorization Code获取Access Token 




#### 获取Authorization Code

GET  https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=101913612&redirect_uri=http://www.meiduo.site:8000/oauth_callback&state=next
  // state参数作用就是访问你这个url后，可以取这个state的值。比如点用户中心/users/info/跳转来到登录页面/users/login/，所以这个next就是/users/info/
  // 这个是GET请求作用：提供扫码页面的。扫码页面有腾讯那边提供的

| 参数          | 是否必须 | 含义                                                         |
| ------------- | -------- | ------------------------------------------------------------ |
| response_type | 必须     | 授权类型，此值固定为“code”。                                 |
| client_id     | 必须     | 申请QQ登录成功后，分配给应用的appid。                        |
| redirect_uri  | 必须     | 成功授权后的回调地址，必须是注册appid时填写的主域名下的地址，建议设置为网站首页或网站的用户中心。注意需要将url进行URLEncode。 |
| state         | 必须     | client端的状态值。用于第三方应用防止CSRF攻击，成功授权后回调时会原样带回。请务必严格按照流程检查用户与state参数状态的绑定。 |

返回的： http://graph.qq.com/demo/index.jsp?code=9A5F************************06AF&state=next   # code就是所要获取得到的Authorization Code
 // 通过上面这个提供扫码页面的url，等成功授权即登录后就会自己去访问redirect_uri：http://www.meiduo.site:8000/oauth_callback？code=9A5F************************06AF&state=next
 

#### 通过Authorization Code获取Access Token

GET  https://graph.qq.com/oauth2.0/token?grant_type=authorization_code&client_id=101913612&client_secret=39eb6ac28cb343b3e5562ef1032b7cab&code=9A5F************************06AF&redirect_uri=回调地址



| 参数          | 是否必须 | 含义                                                         |
| ------------- | -------- | ------------------------------------------------------------ |
| grant_type    | 必须     | 授权类型，在本步骤中，此值为“authorization_code”。           |
| client_id     | 必须     | 申请QQ登录成功后，分配给网站的appid。                        |
| client_secret | 必须     | 申请QQ登录成功后，分配给网站的appkey。                       |
| code          | 必须     | 上一步返回的authorization code。 如果用户成功登录并授权，则会跳转到指定的回调地址，并在URL中带上Authorization Code。 例如，回调地址为www.qq.com/my.php，则跳转到： http://www.qq.com/my.php?code=520DD95263C1CFEA087****** 注意此code会在10分钟内过期。 |
| redirect_uri  | 必须     | 与上面一步中传入的redirect_uri保持一致。                     |



获取到Access Token



### 得到对应用户身份的OpenID 。这个OpenID是腾讯那边这个QQ的数据库里面的id

GET  https://graph.qq.com/oauth2.0/me?access_token=access_token



| 参数         | 是否必须 | 含义                            |
| ------------ | -------- | ------------------------------- |
| access_token | 必须     | 上一步中获取到的access token。  |

```
callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} );
```

















