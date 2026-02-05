# AI模型性能拨测系统

一个基于 Flask 的 AI 模型性能测试工具，支持用户注册登录、模型性能测试、历史记录保存和分享功能。

## 功能特性

### 用户系统
- 邮箱验证码注册/登录
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

3. 启动应用
```bash
python app.py
```

4. 访问系统
打开浏览器访问: http://localhost:5001

### Docker 部署

```bash
docker build -t ai-monitor .
docker run -p 5001:5001 -e SMTP_USERNAME=xxx -e SMTP_PASSWORD=xxx ai-monitor
```

## API 接口

### 用户认证
- **POST** `/api/auth/send-code` - 发送验证码
- **POST** `/api/auth/register` - 注册/登录
- **POST** `/api/auth/logout` - 退出登录
- **GET** `/api/auth/me` - 获取当前用户信息

### 测试
- **GET** `/api/test/limit` - 获取测试限制信息
- **POST** `/api/test/submit` - 提交测试结果
- **GET** `/api/test/history` - 获取测试历史（需登录）
- **GET** `/api/test/share/<token>` - 获取分享的测试结果

## 数据库结构

### users 表
- id: 用户ID
- email: 邮箱地址
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
