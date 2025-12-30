# AI模型性能拨测系统

一个基于Flask的AI模型性能监控和拨测工具，支持多种AI模型提供商的实时性能测试、定时任务管理和可视化报告。

## 功能特性

### 手动测试
- 支持单模型或多模型同时测试
- 支持多种AI模型提供商：
  - DeepSeek
  - OpenAI
  - Anthropic
  - 自定义模型
- 自定义JSON请求格式
- 实时性能指标统计

### 计划任务
- 创建定时测试任务
- 灵活的测试间隔设置（5分钟-1440分钟）
- 任务管理（创建、编辑、删除）
- 自动执行并保存测试结果

### 性能报告
- 可视化图表展示
- 历史数据查询
- 多维度性能指标分析

## 性能指标

系统提供以下性能指标：
- **平均延迟** (Avg Latency)
- **P90延迟** (90th Percentile)
- **P99延迟** (99th Percentile)
- **最小延迟** (Min Latency)
- **最大延迟** (Max Latency)
- **错误率** (Error Rate)
- **成功次数** (Success Count)
- **失败次数** (Error Count)

## 技术栈

- **后端框架**: Flask
- **数据库**: SQLite
- **前端框架**: Bootstrap 5
- **图表库**: Chart.js
- **任务调度**: schedule
- **HTTP客户端**: requests
- **数据处理**: numpy

## 项目结构

```
ai-monitor/
├── app.py              # Flask应用主文件
├── database.py         # 数据库操作类
├── scheduler.py        # 任务调度器
├── requirements.txt    # Python依赖
├── ai_monitor.db      # SQLite数据库文件
├── templates/
│   └── index.html     # 前端界面
├── static/
│   ├── css/           # 样式文件
│   ├── js/            # JavaScript文件
│   └── fonts/         # 字体文件
└── README.md          # 项目文档
```

## 安装部署

### 环境要求
- Python 3.6+
- pip

### 安装步骤

1. 克隆项目
```bash
cd ai-monitor
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 启动应用
```bash
python app.py
```

4. 访问系统
打开浏览器访问: http://localhost:5001

## API接口

### 手动测试
- **POST** `/test_model`
  - 请求体: `{"model_provider": "deepseek", "model_url": "...", "api_key": "...", "test_count": 10}`
  - 响应: 性能测试结果

### 计划任务管理
- **GET** `/api/tasks` - 获取所有任务
- **POST** `/api/tasks` - 创建新任务
- **PUT** `/api/tasks/<id>` - 更新任务
- **DELETE** `/api/tasks/<id>` - 删除任务
- **GET** `/api/tasks/<id>/results` - 获取任务测试结果

### 测试结果
- **GET** `/api/results` - 获取所有测试结果
- **GET** `/api/results?task_id=<id>` - 获取指定任务的测试结果

## 数据库结构

### tasks表
- id: 任务ID
- name: 任务名称
- model_provider: 模型提供商
- model_url: 模型API地址
- api_key: API密钥
- test_count: 测试次数
- interval: 测试间隔（分钟）
- is_active: 是否激活
- created_at: 创建时间
- updated_at: 更新时间

### test_results表
- id: 结果ID
- task_id: 关联任务ID
- test_time: 测试时间
- total_tests: 总测试次数
- success_count: 成功次数
- error_count: 失败次数
- error_rate: 错误率
- latency_stats: 延迟统计（JSON格式）

## 使用说明

### 手动测试
1. 在"手动测试"标签页配置模型参数
2. 选择模型提供商或使用自定义模型
3. 输入模型URL和API Key
4. 设置测试次数
5. 点击"开始测试"按钮
6. 查看实时测试结果

### 创建计划任务
1. 在"计划任务"标签页填写任务信息
2. 设置任务名称、测试间隔、测试次数
3. 配置模型参数
4. 点击"创建任务"
5. 系统将自动按设定间隔执行测试

### 查看性能报告
1. 在"性能报告"标签页选择任务
2. 查看历史测试数据
3. 分析性能趋势

## 注意事项

- API Key请妥善保管，不要泄露
- 测试间隔建议不低于5分钟
- 数据库文件会自动创建，无需手动配置
- 调度器线程在应用启动时自动启动
- 修改任务后会自动重新加载调度器

## 许可证

MIT License
