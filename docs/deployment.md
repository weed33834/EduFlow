# 部署文档

> 文档版本: v1.0 | 最后更新: 2026-08-09

---

## 目录

1. [部署方式概览](#1-部署方式概览)
2. [Docker 部署](#2-docker-部署)
3. [手动部署](#3-手动部署)
4. [Kubernetes 部署](#4-kubernetes-部署)
5. [环境变量说明](#5-环境变量说明)
6. [数据库迁移](#6-数据库迁移)
7. [监控与维护](#7-监控与维护)

---

## 1. 部署方式概览

EduFlow 畅学 支持以下三种部署方式：

| 部署方式 | 适用场景 | 复杂度 | 推荐用途 |
|----------|----------|--------|----------|
| Docker Compose | 开发环境 / 小型部署 | 低 | 本地开发、测试、演示 |
| 手动部署 | 自定义环境 | 中 | 特殊网络环境、定制化部署 |
| Kubernetes | 生产环境 / 大规模部署 | 高 | 线上正式环境、弹性伸缩 |

---

## 2. Docker 部署

### 2.1 前置要求

- Docker >= 20.10
- Docker Compose >= 2.0
- 至少 4 GB 可用内存（推荐 8 GB）
- 至少 20 GB 可用磁盘空间

### 2.2 快速部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-org/eduflow.git
cd eduflow

# 2. 复制环境变量配置
cp .env.example .env
# 编辑 .env 文件，修改必要的配置项（详见环境变量说明章节）

# 3. 启动所有服务
docker-compose up -d

# 4. 初始化数据库
docker-compose exec backend alembic upgrade head

# 5. 导入初始数据
docker-compose exec backend python scripts/seed_data.py

# 6. 验证部署
curl http://localhost:8000/api/v1/health
```

### 2.3 服务组件

```yaml
# docker-compose.yml 主要服务组件
services:
  # API 网关
  kong:
    image: kong:3.5
    ports:
      - "8000:8000"   # 对外 API 端口
      - "8001:8001"   # Kong Admin API

  # 后端服务
  backend:
    build: ./backend
    env_file: .env
    depends_on:
      - postgres
      - redis
      - rabbitmq

  # AI 智能体服务
  ai-agent:
    build: ./ai-agent
    env_file: .env
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # 前端服务
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    env_file: .env

  # 基础设施
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  milvus:
    image: milvusdb/milvus:v2.3.0

  rabbitmq:
    image: rabbitmq:3.12-management
```

### 2.4 部分启动

如果只需要启动部分服务（例如仅启动后端及依赖的基础设施），可以使用：

```bash
# 仅启动后端相关服务
docker-compose up -d postgres redis rabbitmq milvus backend

# 仅启动 AI 智能体服务
docker-compose up -d postgres redis milvus rabbitmq ai-agent

# 仅启动前端
docker-compose up -d frontend
```

### 2.5 常用 Docker 命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart backend

# 重新构建并启动
docker-compose up -d --build backend

# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

---

## 3. 手动部署

### 3.1 前置要求

- Python >= 3.11
- Node.js >= 18.0.0
- pnpm >= 8.0.0
- PostgreSQL >= 15
- Redis >= 7.0
- RabbitMQ >= 3.12
- Milvus >= 2.3.0
- Nginx >= 1.24

### 3.2 后端部署

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境并安装依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-prod.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置生产环境参数

# 4. 初始化数据库
alembic upgrade head

# 5. 启动服务（使用 Gunicorn + Uvicorn）
gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

### 3.3 AI 智能体服务部署

```bash
# 1. 进入 AI 智能体目录
cd ai-agent

# 2. 安装依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 配置 LLM API Key 等参数

# 4. 启动智能体服务
python -m agents.runner \
  --workers 2 \
  --queue rabbitmq://localhost:5672
```

### 3.4 前端部署

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
pnpm install

# 3. 构建生产版本
pnpm build

# 4. 使用 PM2 启动 Next.js 服务
npm install -g pm2
pm2 start npm --name "eduflow-frontend" -- start
pm2 save
```

### 3.5 Nginx 反向代理配置

```nginx
# /etc/nginx/sites-available/eduflow.conf

upstream backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;  # 多实例负载均衡
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name eduflow.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name eduflow.example.com;

    ssl_certificate /etc/ssl/certs/eduflow.crt;
    ssl_certificate_key /etc/ssl/private/eduflow.key;

    # API 请求转发
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }

    # AI 智能体 API
    location /api/v1/agents/ {
        proxy_pass http://backend;
        proxy_read_timeout 300s;  # AI 响应可能较慢
    }

    # 静态资源
    location /_next/ {
        proxy_pass http://frontend;
        proxy_cache static_cache;
        proxy_cache_valid 200 60m;
    }

    # 前端页面
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 4. Kubernetes 部署

### 4.1 前置要求

- Kubernetes 集群 >= 1.28
- kubectl 已配置
- Helm >= 3.0
- Ingress Controller（如 Nginx Ingress）
- 存储类（StorageClass）已配置

### 4.2 部署步骤

```bash
# 1. 创建命名空间
kubectl create namespace eduflow

# 2. 部署基础设施
# PostgreSQL
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgresql bitnami/postgresql \
  --namespace eduflow \
  --set auth.database=eduflow \
  --set auth.username=eduflow \
  --set primary.persistence.size=50Gi

# Redis
helm install redis bitnami/redis \
  --namespace eduflow \
  --set architecture=standalone

# RabbitMQ
helm install rabbitmq bitnami/rabbitmq \
  --namespace eduflow

# 3. 部署应用服务
kubectl apply -f deploy/kubernetes/ -n eduflow

# 4. 配置 Ingress
kubectl apply -f deploy/kubernetes/ingress.yaml -n eduflow

# 5. 验证部署
kubectl get pods -n eduflow
kubectl get ingress -n eduflow
```

### 4.3 Kubernetes 资源配置示例

```yaml
# deploy/kubernetes/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: eduflow-backend
  labels:
    app: eduflow-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: eduflow-backend
  template:
    metadata:
      labels:
        app: eduflow-backend
    spec:
      containers:
        - name: backend
          image: eduflow/backend:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: eduflow-secrets
                  key: database-url
            - name: REDIS_URL
              value: "redis://redis:6379"
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "2"
              memory: "2Gi"
          livenessProbe:
            httpGet:
              path: /api/v1/health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/v1/health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
```

---

## 5. 环境变量说明

### 5.1 通用环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `ENVIRONMENT` | 是 | `development` | 运行环境 (`development`/`staging`/`production`) |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别 (`DEBUG`/`INFO`/`WARNING`/`ERROR`) |
| `SECRET_KEY` | 是 | - | JWT 加密密钥，生产环境务必修改 |
| `ALLOWED_HOSTS` | 是 | `*` | 允许的 Host 列表，逗号分隔 |

### 5.2 数据库

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `DATABASE_URL` | 是 | - | PostgreSQL 连接字符串 |
| `DATABASE_POOL_SIZE` | 否 | `20` | 数据库连接池大小 |
| `DATABASE_MAX_OVERFLOW` | 否 | `10` | 连接池最大溢出数 |

### 5.3 Redis

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `REDIS_URL` | 是 | `redis://localhost:6379/0` | Redis 连接地址 |
| `REDIS_PASSWORD` | 否 | - | Redis 密码 |

### 5.4 RabbitMQ

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `RABBITMQ_URL` | 是 | `amqp://guest:guest@localhost:5672/` | RabbitMQ 连接地址 |
| `RABBITMQ_QUEUE_PREFIX` | 否 | `eduflow` | 队列名称前缀 |

### 5.5 Milvus 向量数据库

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `MILVUS_HOST` | 是 | `localhost` | Milvus 服务地址 |
| `MILVUS_PORT` | 否 | `19530` | Milvus gRPC 端口 |
| `MILVUS_COLLECTION` | 否 | `knowledge_base` | 默认集合名称 |

### 5.6 AI / LLM

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `LLM_PROVIDER` | 是 | `openai` | LLM 提供商 (`openai`/`wenxin`/`azure`) |
| `OPENAI_API_KEY` | 否 | - | OpenAI API Key |
| `OPENAI_MODEL` | 否 | `gpt-4o` | OpenAI 模型名称 |
| `WENXIN_API_KEY` | 否 | - | 文心一言 API Key |
| `WENXIN_SECRET_KEY` | 否 | - | 文心一言 Secret Key |
| `EMBEDDING_MODEL` | 否 | `text-embedding-3-large` | 向量嵌入模型 |

### 5.7 对象存储

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `STORAGE_BACKEND` | 是 | `local` | 存储后端 (`local`/`s3`/`oss`) |
| `S3_ENDPOINT` | 否 | - | S3 兼容存储端点 |
| `S3_ACCESS_KEY` | 否 | - | S3 Access Key |
| `S3_SECRET_KEY` | 否 | - | S3 Secret Key |
| `S3_BUCKET` | 否 | `eduflow` | S3 Bucket 名称 |

### 5.8 邮件/通知

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `SMTP_HOST` | 否 | - | SMTP 服务器地址 |
| `SMTP_PORT` | 否 | `587` | SMTP 端口 |
| `SMTP_USER` | 否 | - | SMTP 用户名 |
| `SMTP_PASSWORD` | 否 | - | SMTP 密码 |
| `SMTP_FROM` | 否 | - | 发件人地址 |

### 5.9 前端

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `NEXT_PUBLIC_API_URL` | 是 | `http://localhost:8000` | API 服务地址 |
| `NEXT_PUBLIC_WS_URL` | 是 | `ws://localhost:8000` | WebSocket 服务地址 |
| `NEXT_PUBLIC_CDN_URL` | 否 | - | CDN 资源地址 |

---

## 6. 数据库迁移

### 6.1 执行迁移

```bash
# 生成迁移脚本
alembic revision --autogenerate -m "add_course_table"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

### 6.2 数据初始化

```bash
# 导入初始数据（管理员账号、默认配置等）
python scripts/seed_data.py

# 导入测试数据（开发环境）
python scripts/seed_test_data.py
```

### 6.3 数据库备份

```bash
# 备份
pg_dump -U eduflow -d eduflow_prod > backup/eduflow_$(date +%Y%m%d).sql

# 恢复
psql -U eduflow -d eduflow_prod < backup/eduflow_20260809.sql
```

---

## 7. 监控与维护

### 7.1 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/api/v1/health

# 预期响应
# {"status": "ok", "version": "0.1.0", "timestamp": "2026-08-09T12:00:00Z"}
```

### 7.2 日志查看

```bash
# Docker 环境
docker-compose logs -f --tail=100 backend

# 手动部署
tail -f logs/access.log
tail -f logs/error.log

# Kubernetes
kubectl logs -f deployment/eduflow-backend -n eduflow
```

### 7.3 性能监控

- **Prometheus 指标**: 所有服务暴露 `/metrics` 端点，提供 Prometheus 标准格式指标。
- **Grafana 看板**: 预置的 Grafana Dashboard 提供 CPU、内存、请求量、延迟等可视化监控。
- **告警规则**: 配置了服务宕机、高延迟、错误率飙升等告警。

### 7.4 常见问题排查

| 问题 | 可能原因 | 解决方法 |
|------|---------|----------|
| 服务启动失败 | 数据库连接失败 | 检查 `DATABASE_URL` 是否正确，数据库是否可访问 |
| API 返回 401 | Token 过期或无效 | 检查 `SECRET_KEY` 配置，重新登录获取 Token |
| AI 智能体响应超时 | LLM API 不可用 | 检查 API Key 和配额，查看 LLM 服务状态 |
| 视频上传失败 | 存储服务异常 | 检查存储后端配置，确认磁盘空间或 S3 访问权限 |
| 页面加载慢 | 前端静态资源未缓存 | 配置 CDN 或 Nginx 缓存策略 |

---

> 如有部署相关问题，请提交 [GitHub Issue](https://github.com/your-org/eduflow/issues) 或发送邮件至 maintainers@eduflow.dev。