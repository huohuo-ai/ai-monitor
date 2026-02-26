# 系统配置

# 微信公众账号配置
# 重要：需要在微信公众平台进行以下配置：
# 1. 设置 -> 公众号设置 -> 功能设置 -> 网页授权域名 -> 添加你的域名
# 2. 开发 -> 基本配置 -> 获取 AppID 和 AppSecret
# 3. 本地测试需要使用内网穿透工具（如 ngrok），并将生成的域名配置到网页授权域名
WECHAT_CONFIG = {
    'app_id': 'wxea13bb2c75b937a8',
    'app_secret': '03168a006a802b11a4d73c12e1f77d48',
    # 授权回调域名，需要在微信公众平台配置
    # 格式：http://你的域名/api/auth/wechat/callback
    # 本地测试可以使用内网穿透工具，如 ngrok，然后填写：http://xxx.ngrok.io/api/auth/wechat/callback
    'redirect_uri': 'http://site.huaqiang.art/api/auth/wechat/callback',
    # 授权作用域：
    # - snsapi_base：静默授权，无需用户点击同意，但只能获取openid
    # - snsapi_userinfo：需要用户点击同意，可以获取用户昵称和头像
    'scope': 'snsapi_userinfo',
}

# 微信开放平台配置（用于PC浏览器扫码登录）
# 如需在PC浏览器使用微信扫码登录，需要：
# 1. 访问 https://open.weixin.qq.com 注册成为开发者
# 2. 创建网站应用，获取 AppID 和 AppSecret
# 3. 设置回调域名
WECHAT_OPEN_CONFIG = {
    # 注意：这里需要填写微信开放平台的 AppID（不是公众号的）
    # 格式：wx + 16位小写字母数字组合
    'app_id': 'wxc8851e4d9a983a3e',  # 例如：'wx1234567890abcdef'
    'app_secret': '5ee5b8a728635698bc20c2070f518cad',
    # 授权回调地址，需要在微信开放平台配置
    'redirect_uri': 'http://site.huaqiang.art/api/auth/wechat/open/callback',
}

# 广告位配置
AD_CONFIG = {
    # 总开关：是否启用广告位
    'enabled': True,
    
    # 广告位标题
    'title': '🚀 推荐服务',
    
    # 广告列表
    'ads': [
        {
            'icon': 'bi-robot',
            'name': 'DeepSeek API',
            'desc': '国产大模型，性价比之选',
            'url': 'https://platform.deepseek.com/',
            'badge': '热门',
            'badge_color': 'danger'
        },
        {
            'icon': 'bi-lightning-charge',
            'name': 'Kimi API',
            'desc': 'Moonshot AI，长文本专家',
            'url': 'https://platform.moonshot.cn/',
            'badge': None,
            'badge_color': None
        },
        {
            'icon': 'bi-globe',
            'name': 'OpenRouter',
            'desc': '一站式接入多种大模型',
            'url': 'https://openrouter.ai/',
            'badge': '聚合',
            'badge_color': 'info'
        },
        {
            'icon': 'bi-cpu',
            'name': 'SiliconFlow',
            'desc': '开源模型推理服务',
            'url': 'https://siliconflow.cn/',
            'badge': None,
            'badge_color': None
        }
    ]
}
