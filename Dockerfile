FROM python:3.9-slim

WORKDIR /app

# 复制requirements.txt并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建临时目录
RUN mkdir -p temp_pdfs

# 暴露端口
EXPOSE 5001

# 运行应用
CMD ["python", "app.py"]
