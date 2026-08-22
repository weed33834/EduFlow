# 全量工程审计报告（v0.4.x 线）

审计范围：`git ls-files` 全部 70 个受管文件，无一跳过。
时间：2026-08；执行：ox-alpha 自动化审计 + 人工复核。

## 一、发现与处置对照表

| # | 类别 | 发现 | 处置 | 提交 |
|---|---|---|---|---|
| 1 | 虚假实现 | 无 stub/mock/fake/placeholder 占位逻辑（全仓扫描 + agentseed 双工具验证） | — | — |
| 2 | 静默吞错 | nodes.py recall×2 / reflect×1 裸 `except: pass` | 补 warning 日志，降级行为不变 | v0.4.12 |
| 3 | 重复造轮子 | teach/respond 各写一份历史截取循环 | 抽 `_recent_messages()` | v0.4.13 |
| 4 | 重复造轮子 | chat.py 两处 FSRS tzinfo 剥离 | 抽 `_naive_due()` | v0.4.14 |
| 5 | 协议漂移 | 前端 ChatResponseData 含后端从不发送的事件类型，缺 judged 字段 | 类型对齐实际 SSE 协议 | v0.4.15 |
| 6 | CI 形同虚设 | backend job 只 compileall，80 个测试从未在 CI 运行 | 冷装 venv + pytest 步骤 | v0.4.16 |
| 7 | 供应链风险 | dependabot 允许 pip semver-minor 自动合并且无测试兜底——正是历史上 3 个 API 断裂 bug 的复发通道 | auto-merge 收紧为 patch-only | v0.4.16 |
| 8 | 可观测缺口 | 外部追踪（LangSmith/Langfuse）无接入点 | litellm success_callback 环境变量透传，默认零开销 | v0.4.17 |
| 9 | 架构边界 | 限流为进程内计数，多 worker 各自独立 | 可选 Redis ZSET 分布式实现，fail-open | v0.4.18 |
| 10 | 实现缺陷（新引入即修） | Redis 限流 member 用 `id(object())` 生成，CPython 地址复用导致 zadd 覆盖 | 改 uuid4 唯一成员 | v0.4.18 |
| 11 | 产品承诺 | 深色模式/移动端未做 | CSS 变量换肤 + ThemeToggle + 首屏防闪白 + 气泡宽度适配 | v0.4.19 |

## 二、逐文件清单与结论

### 后端 app/（18 文件）
| 文件 | 结论 |
|---|---|
| main.py | 生产安全 fail-fast、lifespan 装配 checkpointer 与外部回调 ✅ |
| config.py | 全配置集中、弱密钥生产拒绝启动 ✅ |
| database.py / deps.py / security.py / models.py | 直观无问题；bcrypt 已钉版兼容 passlib ✅ |
| ratelimit.py | 内存+Redis 双实现，接口一致，fail-open 有测试 ✅ |
| agents/state.py · graph.py · nodes.py | 10 节点状态机；判题路由有双保险守卫；无残留裸吞错 ✅ |
| tools/llm.py | JSON mode、真流式、追踪日志、外部回调；死代码 stream_chat 已删 ✅ |
| tools/sandbox.py | e2b 2.x API（files.write+commands.run），语言白名单快速失败 ✅ |
| tools/knowledge.py | query_points API、分块器纯函数、向量直写 ✅ |
| tools/memory.py | AsyncMemory + filters，兼容 dict/list 返回形态 ✅ |
| routers/auth.py · chat.py · sessions.py · profile.py | 限流、判题持久化、FSRS 重排、画像回写均有测试覆盖 ✅ |

### 后端 tests/ scripts/（15 文件）
89 用例全离线通过；评估集 22 严格样本 + 4 已知边界记录。✅

### 前端（17 文件）
api.ts 协议类型已对齐；AuthContext token 校验回退正确；RouteGuard 公开路径守卫；
ErrorBoundary 兜底；ThemeToggle 新增。`npm run build` 全路由通过 ✅。
遗留：`chatStream` 的 POST 重试在网络半途失败时理论上可能造成消息重复入库
（fetch 抛错才重试，概率低）；记录于此，后续可加幂等键。

### 配置 / CI / 文档（20 文件）
docker-compose：Qdrant/Postgres 端口仍映射宿主机且 Postgres 弱口令 —— 开发用途明确，
生产部署文档需强调改密+关端口（记入 TODO，不属本轮 patch）。
Dockerfile ×2、dockerignore ×2：standalone 输出与非 root 用户均正确 ✅。
ci.yml / dependabot*.yml：见处置表 #6/#7 ✅。
README.md：与实现对齐（v0.4.10 复核）✅。VERSIONING.md：大小迭代规则与审计表 ✅。
REBUILD-PLAN.md：**历史设计文档**（1019 行，含已被推翻的旧方案），保留作决策记录，
现状以 README/VERSIONING 为准。
LICENSE：MIT ✅。

## 三、已知边界（诚实声明）

1. LangSmith/Langfuse 仅打通注册机制，未用真实云端账号端到端验证（需账号）。
2. Redis 限流经 fakeredis 验证管线逻辑，未连真实 Redis 实例压测。
3. 前端 npm lockfile 存在 GitHub Dependabot 报告的历史漏洞（47 项）——升级 next/react
   属大迭代范畴，列入 0.5.x 计划，未在本 patch 线强行升。
4. docker-compose 默认口令仅限本地开发。

## 四、验证证据

- 后端：`pytest -q` → 89 passed（全离线）
- 前端：`npm run build` → 全路由编译成功
- 门禁：全部源码过 verify_code（suspects=[]）+ scan_hallucination（clean）
