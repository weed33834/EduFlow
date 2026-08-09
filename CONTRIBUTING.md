# 贡献指南

感谢您对 **EduFlow 畅学** 项目的关注！我们欢迎所有形式的贡献，包括但不限于提交 Bug 报告、功能建议、代码贡献、文档改进等。请花几分钟阅读本指南，以确保协作顺畅高效。

---

## 项目简介

EduFlow 畅学 是一个基于 AI 智能体的下一代在线学习平台，致力于通过人工智能技术为学习者提供个性化、自适应、高效的学习体验。平台采用微服务架构，集成了多个 AI 智能体，覆盖学习路径规划、知识问答、作业批改与学习进度追踪等核心场景。

---

## 开发环境搭建

### 前置要求

- Python >= 3.10
- Node.js >= 18.0.0
- pnpm >= 8.0.0
- Docker & Docker Compose >= 2.0
- PostgreSQL >= 15
- Redis >= 7.0
- Git >= 2.30

### 1. 克隆仓库

```bash
git clone https://github.com/your-org/eduflow.git
cd eduflow
```

### 2. 后端环境配置

```bash
# 创建 Python 虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 复制环境变量模板
cp .env.example .env
# 编辑 .env 文件，填入必要的配置信息
```

### 3. 前端环境配置

```bash
cd frontend
pnpm install
```

### 4. 启动基础设施服务

```bash
cd deploy
docker-compose up -d postgres redis
```

### 5. 初始化数据库

```bash
cd backend
alembic upgrade head
python scripts/seed_data.py
```

### 6. 启动开发服务

```bash
# 终端 1：启动后端服务
cd backend
uvicorn app.main:app --reload --port 8000

# 终端 2：启动 AI 智能体服务
cd backend
python -m agents.runner

# 终端 3：启动前端开发服务
cd frontend
pnpm dev
```

访问 http://localhost:3000 即可查看应用。

---

## 代码规范

### Python 规范

- **格式化**: 使用 [Black](https://github.com/psf/black) 进行代码格式化，行长度限制为 88 字符。
- **导入排序**: 使用 [isort](https://github.com/PyCQA/isort) 对导入进行排序。
- **类型注解**: 所有函数参数和返回值必须添加类型注解。
- **Lint 检查**: 使用 [Ruff](https://github.com/astral-sh/ruff) 进行代码检查。
- **命名约定**:
  - 类名: `PascalCase`
  - 函数/方法: `snake_case`
  - 变量: `snake_case`
  - 常量: `UPPER_SNAKE_CASE`
- **文档字符串**: 使用 Google 风格的文档字符串格式。

```python
# 示例
from typing import Optional


class CourseService:
    """课程服务类，处理课程相关的业务逻辑。"""

    def get_course_by_id(self, course_id: int) -> Optional[dict]:
        """根据课程 ID 获取课程信息。

        Args:
            course_id: 课程的唯一标识符。

        Returns:
            包含课程信息的字典，如果未找到则返回 None。
        """
        ...
```

### TypeScript 规范

- **格式化**: 使用 [Prettier](https://prettier.io/) 进行代码格式化。
- **Lint 检查**: 使用 [ESLint](https://eslint.org/) 配合 `@typescript-eslint` 规则集。
- **类型定义**: 优先使用 `interface` 而非 `type`，避免使用 `any`。
- **命名约定**:
  - 组件名: `PascalCase`
  - 函数/变量: `camelCase`
  - 常量: `UPPER_SNAKE_CASE`
  - 文件命名: 组件文件使用 `PascalCase.tsx`，工具文件使用 `camelCase.ts`
- **React 组件**: 使用函数组件和 Hooks，避免类组件。

```typescript
// 示例
interface Course {
  id: string;
  title: string;
  description: string;
  duration: number;
}

const CourseCard: React.FC<Course> = ({ id, title, description, duration }) => {
  return (
    <div className="course-card">
      <h3>{title}</h3>
      <p>{description}</p>
      <span>{duration} 分钟</span>
    </div>
  );
};
```

### 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

类型说明：

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式调整 |
| `refactor` | 代码重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具链变更 |
| `perf` | 性能优化 |

示例：

```
feat(course): 添加课程推荐功能

- 基于用户学习历史生成个性化推荐
- 支持协同过滤和内容推荐两种算法
- 新增推荐结果缓存机制

Closes #123
```

---

## 提交 PR 流程

1. **Fork 仓库**：将主仓库 Fork 到您的 GitHub 账户。

2. **创建分支**：从 `main` 分支创建您的特性分支。

   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/your-feature-name
   ```

3. **开发与测试**：在您的分支上进行开发，确保：
   - 所有测试通过：`pytest tests/` 和 `pnpm test`
   - 代码通过 Lint 检查：`ruff check .` 和 `pnpm lint`
   - 代码格式化通过：`black .` 和 `pnpm format`
   - 新增功能包含足够的测试覆盖

4. **提交变更**：

   ```bash
   git add .
   git commit -m "feat(scope): 清晰的提交说明"
   ```

5. **推送到远程**：

   ```bash
   git push origin feat/your-feature-name
   ```

6. **创建 Pull Request**：
   - 前往 GitHub 仓库页面，点击 "New Pull Request"
   - 确保 PR 的目标分支为 `main`
   - 填写 PR 模板中的内容
   - 关联相关的 Issue（如有）
   - 添加合适的标签（label）

7. **代码审查**：
   - 至少需要一位维护者批准
   - 所有 CI 检查必须通过
   - 根据审查意见进行修改

8. **合并**：审查通过后，由维护者进行 Squash & Merge。

---

## 分支管理策略

我们采用以下分支管理策略：

### 分支结构

```
main          - 生产环境分支，始终处于可发布状态
├── develop   - 开发主分支，集成所有特性
├── feat/*    - 特性分支，从 develop 分支创建
├── fix/*     - Bug 修复分支
├── docs/*    - 文档更新分支
└── release/* - 发布准备分支
```

### 规则说明

- **main 分支**：受保护，禁止直接推送。仅通过 PR 从 `release/*` 或 `hotfix/*` 合并。
- **develop 分支**：日常开发集成分支，所有 `feat/*` 分支合并至此。
- **feat/* 分支**：从 `develop` 创建，完成后合并回 `develop`。
- **release/* 分支**：从 `develop` 创建，用于发布前的测试和 Bug 修复，完成后合并到 `main` 和 `develop`。
- **hotfix/* 分支**：从 `main` 创建，用于紧急修复生产环境问题，完成后合并到 `main` 和 `develop`。

### 分支命名规范

```
feat/<简要描述>       # 如 feat/course-recommendation
fix/<简要描述>        # 如 fix/login-redirect-error
docs/<简要描述>       # 如 docs/api-docs-update
release/<版本号>      # 如 release/v0.2.0
hotfix/<简要描述>     # 如 hotfix/critical-security-patch
```

---

## 联系方式

如有任何问题或建议，欢迎通过以下方式联系我们：

- **项目维护者邮箱**: maintainers@eduflow.dev
- **项目 Issues**: https://github.com/your-org/eduflow/issues
- **讨论区**: https://github.com/your-org/eduflow/discussions
- **内部沟通**: 加入我们的飞书群组（请联系维护者获取邀请链接）

---

再次感谢您的贡献！您的每一份努力都让 EduFlow 畅学 变得更好。