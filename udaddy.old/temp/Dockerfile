# ---- 1. 使用官方Python镜像作为基础 ----
# 选择一个特定版本的镜像以保证环境一致性，slim版本体积更小
FROM python:3.11-slim

# ---- 2. 设置工作目录 ----
# 容器内所有后续操作的根目录
WORKDIR /app

# ---- 3. 设置环境变量 ----
# 防止Python在容器内生成.pyc文件，保持容器干净
ENV PYTHONDONTWRITEBYTECODE 1
# 确保Python输出是无缓冲的，这对于实时查看容器日志至关重要
ENV PYTHONUNBUFFERED 1

# ---- 4. 复制并安装Python依赖 ----
# 首先只复制需求文件，这是为了利用Docker的层缓存机制。
# 只要requirements.txt文件内容不变，Docker就不会重新执行下面的RUN指令，从而大大加快构建速度。
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- 5. 复制所有应用代码 ----
# 将本地的app目录复制到容器的/app/app目录下
COPY ./app /app/app

# ---- 6. 定义容器默认启动命令 ----
# 这个CMD只是一个默认值。在docker-compose或Kubernetes中，我们会为不同的服务（api, scheduler, worker）
# 提供不同的启动命令来覆盖这个默认值，从而实现用同一个镜像启动不同角色的容器。
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
