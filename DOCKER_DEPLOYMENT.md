# Docker部署指南

## 1. 本地构建Docker镜像

```bash
# 构建镜像
docker build -t ai-monitor:latest .

# 运行容器（基础版）
docker run -d -p 5001:5001 --name ai-monitor ai-monitor:latest

# 运行容器（启用微信登录）
docker run -d -p 5001:5001 \
  -e ENABLE_WECHAT_LOGIN=true \
  --name ai-monitor ai-monitor:latest
```

### 环境变量配置

| 变量名 | 说明 | 默认值 | 可选值 |
|--------|------|--------|--------|
| `ENABLE_WECHAT_LOGIN` | 是否启用微信登录功能 | `false` | `true`/`false` |

## 2. GitHub Actions自动构建配置

### 2.1 配置GitHub Secrets

**重要：这是自动构建的关键步骤，如果不配置Secrets，构建会失败并提示"Username and password required"错误。**

步骤1：进入GitHub仓库页面
步骤2：点击右上角的"Settings"（设置）
步骤3：在左侧导航栏中找到"Secrets and variables"，点击展开
步骤4：选择"Actions"子菜单
步骤5：点击右上角的"New repository secret"按钮
步骤6：分别添加以下两个secrets：

| 变量名 | 值 |
|-------|-----|
| ALIYUN_DOCKER_USERNAME | ithuaqiang@163.com |
| ALIYUN_DOCKER_PASSWORD | whq8273080 |

**注意事项：**
- Secrets名称必须完全匹配上述表格中的变量名（区分大小写）
- Secrets值必须准确无误地复制粘贴
- 确保Secrets是在仓库级别配置的，而不是个人级别
- 配置完成后可以通过再次编辑验证内容是否正确

### 2.2 工作流说明

GitHub Actions工作流配置在 `.github/workflows/docker.yml` 文件中：

- 当代码推送到main分支或创建main分支的PR时触发
- 使用Ubuntu最新版本作为构建环境
- 登录到阿里云容器库 `registry.cn-qingdao.aliyuncs.com`
- 构建Docker镜像并推送至阿里云容器库
- 镜像标签：
  - `registry.cn-qingdao.aliyuncs.com/huaqiangk8s/ai-monitor:latest`
  - `registry.cn-qingdao.aliyuncs.com/huaqiangk8s/ai-monitor:<commit-sha>`

## 3. 手动推送镜像到阿里云容器库（备选方案）

如果GitHub Actions自动构建遇到问题，可以使用以下手动方式构建和推送镜像：

### 3.1 安装Docker

确保您的系统已安装Docker：

```bash
# 检查Docker是否安装
docker --version

# 如果未安装，按照以下方式安装（以Ubuntu为例）
sudo apt-get update
sudo apt-get install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
```

### 3.2 手动构建和推送

```bash
# 1. 登录阿里云容器库
docker login --username=ithuaqiang@163.com --password whq8273080 registry.cn-qingdao.aliyuncs.com

# 2. 构建镜像（使用项目根目录的Dockerfile）
docker build -t registry.cn-qingdao.aliyuncs.com/huaqiangk8s/ai-monitor:latest .

# 3. （可选）同时添加版本标签
docker tag registry.cn-qingdao.aliyuncs.com/huaqiangk8s/ai-monitor:latest registry.cn-qingdao.aliyuncs.com/huaqiangk8s/ai-monitor:v1.0.0

# 4. 推送latest标签
docker push registry.cn-qingdao.aliyuncs.com/huaqiangk8s/ai-monitor:latest

# 5. （可选）推送版本标签
docker push registry.cn-qingdao.aliyuncs.com/huaqiangk8s/ai-monitor:v1.0.0
```

### 3.3 常见问题排查

如果遇到登录问题：
- 检查用户名和密码是否正确
- 确保网络连接正常，能访问阿里云容器库
- 尝试重新获取登录凭证

如果遇到构建问题：
- 检查Dockerfile是否存在且格式正确
- 确保项目依赖完整
- 查看构建日志获取详细错误信息
