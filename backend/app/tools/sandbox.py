"""代码沙箱 — E2B 集成（开源，云端 API）

pip install e2b — 一行装好
GitHub: https://github.com/e2b-dev/E2B
沙箱启动 < 200ms，支持 Python/JS/TS 等
"""
import asyncio
import os
from typing import Optional

try:
    from e2b import Sandbox
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False


async def execute_code(code: str, language: str = "python") -> dict:
    """在 E2B 沙箱中执行代码，返回输出

    不需要自己写沙箱——E2B 是专门为 AI Agent 设计的开源沙箱。
    """
    if not E2B_AVAILABLE or not os.getenv("E2B_API_KEY"):
        return {
            "success": False,
            "stdout": "",
            "stderr": "E2B 沙箱未配置。请 pip install e2b 并设置 E2B_API_KEY。",
            "exit_code": 1,
        }

    def _run():
        with Sandbox() as sandbox:
            if language == "python":
                result = sandbox.run_python(code)
            else:
                result = sandbox.run(language, code)
            return {
                "success": result.exit_code == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
            }

    try:
        return await asyncio.to_thread(_run)
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": 1,
        }


async def is_available() -> bool:
    """检查 E2B 是否可用"""
    return E2B_AVAILABLE and bool(os.getenv("E2B_API_KEY"))
