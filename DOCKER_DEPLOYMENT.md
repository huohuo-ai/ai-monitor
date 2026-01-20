# Docker部署指南

## 1. 本地构建Docker镜像

```bash
# 构建镜像
docker build -t ai-monitor:latest .

# 运行容器
docker run -d -p 5001:5001 --name ai-monitor ai-monitor:latest
```

## 2. GitHub Actions自动构建配置

### 2.1 配置GitHub Secrets

在GitHub仓库的Settings > Secrets and variables > Actions页面添加以下 secrets：

| 变量名 | 值 |
|-------|-----|
| ALIYUN_DOCKER_USERNAME | ithuaqiang@163.com |
| ALIYUN_DOCKER_PASSWORD | whq8273080 |

### 2.2 工作流说明

GitHub Actions工作流配置在 `.github/workflows/docker.yml` 文件中：

- 当代码推送到main分支或创建main分支的PR时触发
- 使用Ubuntu最新版本作为构建环境
- 登录到阿里云容器库 `registry.cn-qingdao.aliyuncs.com`
- 构建Docker镜像并推送至阿里云容器库
- 镜像标签：
  - `registry.cn-qingdao.aliyuncs.com/huaqiangk8s/ai-monitor:latest`
  - `registry.cn-qingdao.aliyuncs.com/huaqiangk8s/ai-monitor:<commit-sha>`

## 3. 手动推送镜像到阿里云容器库

```bash
# 登录阿里云容器库
docker login --username=ithuaqiang@163.com --password whq8273080 registry.cn-qingdao.aliyuncs.com

# 构建镜像
docker build -t registry.cn-qingdao.aliyuncs.com/huaqiangk8s/ai-monitor:latest .

# 推送镜像
docker push registry.cn-qingdao.aliyuncs.com/huaqiangk8s/ai-monitor:latest
```
