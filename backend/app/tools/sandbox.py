"""代码沙箱 — E2B 集成（开源，云端 API）

适配 e2b==2.44.0：
- 2.x 移除了 Sandbox.run_python()，统一走 files.write + commands.run
- CommandResult 字段：stdout / stderr / exit_code / error

pip install e2b — 一行装好
GitHub: https://github.com/e2b-dev/E2B
"""
import asyncio
import logging
import os
import uuid

try:
    from e2b import Sandbox
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False

logger = logging.getLogger(__name__)

# 语言 → (文件名, 执行命令)
_RUNNERS = {
    "python": ("main.py", "python {path}"),
    "javascript": ("main.js", "node {path}"),
    "js": ("main.js", "node {path}"),
}

_COMMAND_TIMEOUT_SECONDS = 30


async def execute_code(code: str, language: str = "python") -> dict:
    """在 E2B 沙箱中执行代码，返回输出

    不需要自己写沙箱——E2B 是专门为 AI Agent 设计的开源沙箱。
    """
    runner = _RUNNERS.get(language)
    if runner is None:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"暂不支持的语言: {language}（支持: {', '.join(_RUNNERS)}）",
            "exit_code": 1,
        }

    if not E2B_AVAILABLE or not os.getenv("E2B_API_KEY"):
        return {
            "success": False,
            "stdout": "",
            "stderr": "E2B 沙箱未配置。请 pip install e2b 并设置 E2B_API_KEY。",
            "exit_code": 1,
        }

    filename, command_tpl = runner
    path = f"/tmp/{uuid.uuid4().hex}-{filename}"

    def _run():
        with Sandbox() as sandbox:
            sandbox.files.write(path, code)
            result = sandbox.commands.run(
                command_tpl.format(path=path),
                timeout=_COMMAND_TIMEOUT_SECONDS,
            )
            return {
                "success": result.exit_code == 0,
                "stdout": result.stdout,
                "stderr": result.stderr or result.error,
                "exit_code": result.exit_code,
            }

    try:
        return await asyncio.to_thread(_run)
    except Exception as e:
        logger.warning("沙箱执行失败 language=%s", language, exc_info=True)
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": 1,
        }


async def is_available() -> bool:
    """检查 E2B 是否可用"""
    return E2B_AVAILABLE and bool(os.getenv("E2B_API_KEY"))
