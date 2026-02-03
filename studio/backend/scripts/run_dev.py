#!/usr/bin/env python3
"""
开发服务器启动脚本
"""
import os
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn


def main():
    """启动开发服务器。"""
    # 设置环境变量
    os.environ.setdefault("DIP_STUDIO_DEBUG", "true")
    os.environ.setdefault("DIP_STUDIO_LOG_LEVEL", "DEBUG")
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
    )


if __name__ == "__main__":
    main()
