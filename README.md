# AI模型性能拨测系统

一个基于 Flask 的 AI 模型性能测试工具，支持用户注册登录、模型性能测试、历史记录保存和分享功能。

## 功能特性

### 用户系统
- 邮箱验证码注册/登录
- 微信公众号授权登录（微信内使用）
- 微信扫码登录（PC浏览器，需配置开放平台）
- 注册用户每日 10 次测试额度
- 非注册用户每日 3 次测试额度

### 模型测试
- 支持多种 AI 模型提供商：
  - DeepSeek
  - OpenAI
  - Kimi
  - Anthropic
  - 自定义模型
- 多模型同时测试对比
- API Key 由前端直接请求模型厂商，**后端不存储 API Key**

### 性能指标
- **平均延迟** (Avg Latency)
- **P90/P99 延迟** (Percentile Latency)
- **TTFT** (Time to First Token)
- **Token 吞吐** (Tokens/Second)
- **错误率** (Error Rate)

### 历史与分享
- 测试历史长期保存
- 生成分享链接，可通过 URL 分享测试结果

## 技术栈

- **后端框架**: Flask
- **数据库**: SQLite
- **前端框架**: Bootstrap 5
- **任务调度**: 前端 JavaScript

## 安装部署

### 环境要求
- Python 3.9+
- pip

### 安装步骤

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置邮件服务（可选）
```bash
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your_email@gmail.com
export SMTP_PASSWORD=your_app_password
export FROM_EMAIL=your_email@gmail.com
```

如果不配置邮件服务，系统将使用模拟模式，验证码将显示在控制台日志中。

3. 配置微信登录（可选）
```bash
# 在 config.py 中修改 WECHAT_CONFIG 的 redirect_uri
# 例如：http://your-domain.com/api/auth/wechat/callback
# 注意：需要在微信公众平台配置网页授权域名
```

4. 启动应用
```bash
python app.py
```

5. 访问系统
打开浏览器访问: http://localhost:5001

### Docker 部署

```bash
docker build -t ai-monitor .
        docker run -d --name $CONTAINER_NAME -p 5001:5001 \
        -e FLASK_DEBUG=1 \
        -e SMTP_SERVER= \
        -e SMTP_PORT=465 \
        -e SMTP_USERNAME= \
        -e SMTP_PASSWORD= \
        -e FROM_EMAIL= \
        -e ENABLE_WECHAT_LOGIN=true \
        $IMAGE_NAME
```

## API 接口

### 用户认证
- **POST** `/api/auth/send-code` - 发送验证码
- **POST** `/api/auth/register` - 注册/登录
- **POST** `/api/auth/logout` - 退出登录
- **GET** `/api/auth/me` - 获取当前用户信息
- **GET** `/api/auth/wechat/login` - 微信公众号登录（微信内）
- **GET** `/api/auth/wechat/open/login` - 微信开放平台扫码登录（PC浏览器）

### 测试
- **GET** `/api/test/limit` - 获取测试限制信息
- **POST** `/api/test/submit` - 提交测试结果
- **GET** `/api/test/history` - 获取测试历史（需登录）
- **GET** `/api/test/share/<token>` - 获取分享的测试结果

## 数据库结构

### users 表
- id: 用户ID
- email: 邮箱地址
- wechat_openid: 微信openid
- wechat_nickname: 微信昵称
- wechat_headimgurl: 微信头像
- created_at: 创建时间
- last_login: 最后登录时间

### test_records 表
- id: 记录ID
- user_id: 用户ID（可为空，表示匿名用户）
- ip: 用户IP（匿名用户使用）
- test_date: 测试日期
- test_count: 测试次数
- models_count: 模型数量
- results: 测试结果（JSON）
- created_at: 创建时间

### share_tokens 表
- id: 记录ID
- record_id: 关联的测试记录ID
- token: 分享 token
- created_at: 创建时间
- expires_at: 过期时间

## 微信登录配置

### 方式一：公众号网页授权（微信内使用）
适用于在微信内置浏览器中访问网站。

#### 配置步骤：
1. 登录微信公众平台
2. 设置 -> 公众号设置 -> 功能设置 -> 网页授权域名
3. 添加你的域名（如：`your-domain.com`）
4. 修改 `config.py` 中的 `WECHAT_CONFIG['redirect_uri']`

#### 本地测试：
1. 使用内网穿透工具（如 ngrok）
2. 运行 `ngrok http 5001` 获取临时域名
3. 将临时域名配置到微信公众平台的网页授权域名
4. 修改 `config.py` 中的 `redirect_uri`：
   ```python
   'redirect_uri': 'https://xxx.ngrok.io/api/auth/wechat/callback'
   ```

### 方式二：微信开放平台扫码登录（PC浏览器使用）
适用于在 Chrome、Safari 等 PC 浏览器中显示微信二维码扫码登录。

#### 配置步骤：
1. 访问 [微信开放平台](https://open.weixin.qq.com)
2. 注册开发者账号并认证
3. 创建**网站应用**
4. 获取 AppID 和 AppSecret
5. 设置回调域名
6. 填写 `config.py` 中的 `WECHAT_OPEN_CONFIG`：
   ```python
   WECHAT_OPEN_CONFIG = {
       'app_id': 'wx1234567890abcdef',
       'app_secret': 'your_app_secret',
       'redirect_uri': 'https://your-domain.com/api/auth/wechat/open/callback',
   }
   ```

#### 登录流程：
1. 用户点击"微信扫码登录"按钮
2. 页面显示微信登录二维码
3. 用户使用微信扫一扫
4. 扫码确认后自动登录
5. 支持获取微信昵称和头像

#### 注意事项：
- 如果没有配置开放平台，PC 浏览器会提示使用邮箱登录
- 二维码有效期为5分钟，过期后可点击刷新
- 系统会自动检测浏览器类型，微信内自动跳转授权

## 安全说明

1. **API Key 安全**: 用户的 API Key 仅在前端使用，直接请求模型厂商服务器，**不会发送到后端服务器**。
2. **验证码**: 验证码 5 分钟有效，只能使用一次。
3. **分享链接**: 分享链接长期有效，包含随机生成的 token。

## 使用说明

1. 在首页配置模型参数（API 地址和 Key）
2. 点击"开始测试"执行测试
3. 测试完成后点击"保存结果"生成分享链接
4. 登录后可查看历史记录

## 许可证

MIT License
