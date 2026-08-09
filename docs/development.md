# 开发指南

> 文档版本: v1.0 | 最后更新: 2026-08-09

---

## 目录

1. [本地开发环境搭建](#1-本地开发环境搭建)
2. [项目结构说明](#2-项目结构说明)
3. [代码规范](#3-代码规范)
4. [测试](#4-测试)
5. [调试技巧](#5-调试技巧)
6. [常见问题](#6-常见问题)

---

## 1. 本地开发环境搭建

### 1.1 前置条件

请确保开发机器已安装以下软件：

| 软件 | 最低版本 | 推荐版本 | 用途 |
|------|----------|----------|------|
| Python | 3.10 | 3.11+ | 后端开发语言 |
| Node.js | 18.0.0 | 20.0.0+ | 前端开发环境 |
| pnpm | 8.0.0 | 9.0.0+ | 前端包管理器 |
| Docker | 20.10 | 24.0+ | 容器化基础设施 |
| Docker Compose | 2.0 | 2.20+ | 多容器管理 |
| Git | 2.30 | 2.40+ | 版本控制 |
| PostgreSQL | 15 | 15+ | 数据库 |
| Redis | 7.0 | 7.2+ | 缓存 |
| RabbitMQ | 3.12 | 3.13+ | 消息队列 |
| Milvus | 2.3.0 | 2.3+ | 向量数据库 |

### 1.2 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/eduflow.git
cd eduflow

# 2. 启动基础设施（PostgreSQL、Redis、RabbitMQ、Milvus）
docker-compose up -d postgres redis rabbitmq milvus

# 3. 配置后端
cd backend
cp .env.example .env
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. 初始化数据库
alembic upgrade head
python scripts/seed_data.py

# 5. 启动后端开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. 配置前端（新终端）
cd frontend
cp .env.example .env.local
pnpm install
pnpm dev
```

### 1.3 配置编辑器

#### VS Code 推荐配置

创建 `.vscode/settings.json`：

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=88"],
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "typescript.updateImportsOnFileMove.enabled": "always",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

推荐安装的扩展：

- **Python** (ms-python.python)
- **Black Formatter** (ms-python.black-formatter)
- **Ruff** (charliermarsh.ruff)
- **Prettier** (esbenp.prettier-vscode)
- **ESLint** (dbaeumer.vscode-eslint)
- **Tailwind CSS IntelliSense** (bradlc.vscode-tailwindcss)
- **Docker** (ms-azuretools.vscode-docker)
- **GitLens** (eamodio.gitlens)

---

## 2. 项目结构说明

```
eduflow/
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── main.py                   # 应用入口
│   │   ├── core/                     # 核心配置
│   │   │   ├── config.py             # 全局配置
│   │   │   ├── security.py           # 认证与安全
│   │   │   └── database.py           # 数据库连接
│   │   ├── models/                   # SQLAlchemy 数据模型
│   │   │   ├── user.py
│   │   │   ├── course.py
│   │   │   └── learning.py
│   │   ├── schemas/                  # Pydantic 数据验证模型
│   │   │   ├── user.py
│   │   │   ├── course.py
│   │   │   └── learning.py
│   │   ├── api/                      # API 路由
│   │   │   ├── v1/
│   │   │   │   ├── users.py
│   │   │   │   ├── courses.py
│   │   │   │   ├── learning.py
│   │   │   │   ├── assessments.py
│   │   │   │   └── agents.py
│   │   │   └── deps.py               # 依赖注入
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── user_service.py
│   │   │   ├── course_service.py
│   │   │   └── learning_service.py
│   │   └── utils/                    # 工具函数
│   │       ├── cache.py
│   │       └── helpers.py
│   ├── migrations/                   # Alembic 数据库迁移
│   │   └── versions/
│   ├── tests/                        # 测试文件
│   │   ├── conftest.py
│   │   ├── test_users/
│   │   ├── test_courses/
│   │   └── test_agents/
│   ├── scripts/                      # 辅助脚本
│   │   ├── seed_data.py
│   │   └── seed_test_data.py
│   ├── requirements.txt              # 生产依赖
│   ├── requirements-dev.txt          # 开发依赖
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                         # 前端应用
│   ├── src/
│   │   ├── app/                      # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── courses/
│   │   │   ├── learning/
│   │   │   └── dashboard/
│   │   ├── components/               # 组件
│   │   │   ├── common/
│   │   │   ├── course/
│   │   │   ├── learning/
│   │   │   └── ai-agent/
│   │   ├── hooks/                    # 自定义 Hooks
│   │   ├── services/                 # API 调用
│   │   ├── stores/                   # 状态管理
│   │   ├── types/                    # TypeScript 类型
│   │   └── utils/                    # 工具函数
│   ├── public/
│   │   ├── images/
│   │   └── fonts/
│   ├── tests/
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── Dockerfile
│
├── ai-agent/                         # AI 智能体服务
│   ├── agents/
│   │   ├── base.py                   # 智能体基类
│   │   ├── learning_path_agent.py    # 学习路径规划智能体
│   │   ├── qa_agent.py               # 智能问答智能体
│   │   ├── assignment_agent.py       # 作业批改智能体
│   │   └── analytics_agent.py        # 学习分析智能体
│   ├── orchestrator/                 # AI 编排引擎
│   │   ├── task_scheduler.py
│   │   └── context_manager.py
│   ├── tools/                        # 智能体工具
│   │   ├── knowledge_retriever.py
│   │   ├── code_analyzer.py
│   │   └── data_aggregator.py
│   ├── models/                       # 模型配置
│   ├── requirements.txt
│   └── Dockerfile
│
├── deploy/                           # 部署配置
│   ├── docker-compose.yml
│   ├── kubernetes/
│   │   ├── backend-deployment.yaml
│   │   ├── frontend-deployment.yaml
│   │   └── ingress.yaml
│   └── nginx/
│       └── eduflow.conf
│
├── docs/                             # 文档
│   ├── architecture.md
│   ├── deployment.md
│   ├── api.md
│   ├── development.md
│   └── ai-agents.md
│
├── .github/                          # GitHub 配置
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
│
├── .gitignore
├── CONTRIBUTING.md
├── CHANGELOG.md
├── README.md
└── LICENSE
```

---

## 3. 代码规范

### 3.1 Python 规范

#### 格式化

使用 Black 作为代码格式化工具，统一代码风格。

```bash
# 格式化所有 Python 文件
black backend/ --line-length=88

# 检查格式问题（不修改）
black backend/ --check --diff
```

#### 导入排序

使用 isort 管理导入语句。

```bash
# 排序导入
isort backend/

# 检查导入排序
isort backend/ --check-only
```

#### Lint 检查

使用 Ruff 进行代码质量检查。

```bash
# 执行检查
ruff check backend/

# 自动修复
ruff check backend/ --fix
```

#### 类型检查

使用 mypy 进行静态类型检查。

```bash
mypy backend/
```

#### 一键运行所有检查

```bash
cd backend
isort .
black .
ruff check --fix .
mypy .
```

### 3.2 TypeScript 规范

#### 格式化

使用 Prettier 进行代码格式化。

```bash
# 格式化所有文件
pnpm format

# 检查格式
pnpm format:check
```

#### Lint 检查

使用 ESLint 进行代码检查。

```bash
# 执行检查
pnpm lint

# 自动修复
pnpm lint:fix
```

#### 类型检查

```bash
pnpm type-check
```

### 3.3 提交规范

项目使用 Commitlint 和 Husky 来确保提交信息符合 Conventional Commits 规范。

```bash
# 安装 Git Hooks
pnpm prepare

# 提交示例
git commit -m "feat(course): 添加课程推荐功能"
git commit -m "fix(login): 修复 OAuth 登录回调错误"
git commit -m "docs: 更新 API 文档中的错误码说明"
```

### 3.4 分支规范

详见 [CONTRIBUTING.md](../CONTRIBUTING.md) 中的分支管理策略章节。

---

## 4. 测试

### 4.1 后端测试

#### 运行测试

```bash
# 运行所有测试
cd backend
pytest

# 运行指定测试文件
pytest tests/test_users/test_user_api.py

# 运行指定测试类
pytest tests/test_users/test_user_api.py::TestUserRegistration

# 运行指定测试方法
pytest tests/test_users/test_user_api.py::TestUserRegistration::test_register_success

# 运行带覆盖率报告
pytest --cov=app --cov-report=term --cov-report=html
```

#### 测试配置

测试配置文件位于 `backend/tests/conftest.py`，包含：

- 测试数据库（使用独立的测试数据库）
- 测试客户端（FastAPI TestClient）
- 认证 Token 生成
- Mock 外部服务

#### 编写测试指南

```python
# tests/test_users/test_user_api.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """测试用户注册成功场景。"""
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "name": "测试用户",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: dict):
    """测试重复邮箱注册失败场景。"""
    response = await client.post("/api/v1/auth/register", json={
        "email": test_user["email"],
        "password": "TestPass123!",
        "name": "重复用户",
    })
    assert response.status_code == 409
    assert "already exists" in response.json()["message"]
```

### 4.2 前端测试

#### 运行测试

```bash
# 运行所有测试
pnpm test

# 运行测试并生成覆盖率报告
pnpm test:coverage

# 运行测试并监听变化
pnpm test:watch
```

#### 组件测试示例

```typescript
// frontend/tests/components/CourseCard.test.tsx
import { render, screen } from '@testing-library/react';
import { CourseCard } from '@/components/course/CourseCard';

describe('CourseCard', () => {
  it('renders course information correctly', () => {
    const course = {
      id: 'c_001',
      title: 'Python 入门',
      description: '从零开始学习 Python',
      difficulty: 'beginner' as const,
      price: 0,
    };

    render(<CourseCard course={course} />);
    expect(screen.getByText('Python 入门')).toBeInTheDocument();
    expect(screen.getByText('免费')).toBeInTheDocument();
  });

  it('displays correct difficulty badge', () => {
    const course = { ...mockCourse, difficulty: 'advanced' };
    render(<CourseCard course={course} />);
    expect(screen.getByText('进阶')).toBeInTheDocument();
  });
});
```

### 4.3 AI 智能体测试

```bash
# 运行智能体单元测试
cd ai-agent
pytest tests/

# 运行特定智能体测试
pytest tests/test_qa_agent.py

# 运行集成测试
pytest tests/integration/
```

### 4.4 端到端测试

```bash
# 安装 Playwright
pnpm exec playwright install

# 运行 E2E 测试
pnpm test:e2e

# 运行带 UI 模式的 E2E 测试
pnpm test:e2e:ui
```

---

## 5. 调试技巧

### 5.1 后端调试

#### VS Code 调试配置

创建 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "cwd": "${workspaceFolder}/backend",
      "envFile": "${workspaceFolder}/backend/.env",
      "justMyCode": true
    },
    {
      "name": "Run Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

#### 使用 PDB

```python
# 在代码中插入断点
import pdb; pdb.set_trace()

# 或使用 Python 3.7+ 内置的 breakpoint()
breakpoint()
```

### 5.2 前端调试

#### React Developer Tools

推荐使用 React Developer Tools 浏览器扩展来检查组件的状态和 props。

#### 网络请求调试

在 `.env.local` 中设置：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
# 开启 API 请求日志
NEXT_PUBLIC_DEBUG=true
```

### 5.3 数据库调试

```bash
# 查看 SQL 查询日志
# 在 .env 中设置
DATABASE_ECHO=true

# 连接数据库
docker-compose exec postgres psql -U eduflow -d eduflow

# 查看慢查询
SELECT * FROM pg_stat_activity WHERE state = 'active';
```

### 5.4 日志查看

```bash
# 后端日志
docker-compose logs -f backend

# RabbitMQ 管理界面
# 访问 http://localhost:15672 (guest/guest)

# Redis 连接测试
redis-cli ping
```

---

## 6. 常见问题

### 6.1 数据库迁移问题

**问题**: `alembic upgrade head` 执行失败

**解决**:
```bash
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 回滚到指定版本
alembic downgrade <revision_id>

# 重新生成迁移
alembic revision --autogenerate -m "description"
```

### 6.2 依赖安装问题

**问题**: pip 安装依赖时出现版本冲突

**解决**:
```bash
# 使用 pip-tools 管理依赖
pip install pip-tools
pip-compile requirements.in
pip-sync requirements.txt
```

### 6.3 Docker 相关问题

**问题**: 容器无法启动

**解决**:
```bash
# 查看容器日志
docker-compose logs <service_name>

# 检查端口占用
lsof -i :8000

# 重建容器
docker-compose up -d --build <service_name>

# 清理 Docker 缓存
docker system prune -a
```

### 6.4 环境变量问题

**问题**: 服务启动报错 "Missing environment variable"

**解决**:
- 确保已复制 `.env.example` 到 `.env`
- 检查 `.env` 文件中的配置项是否正确填写
- 确认 `.env` 文件位于正确的目录

---

> 如果在开发过程中遇到其他问题，请查阅 [项目 Issues](https://github.com/your-org/eduflow/issues) 或联系维护团队。