#!/usr/bin/env python3
"""LingoPDF 启动入口。

用法:
    python run.py            # http://127.0.0.1:8377
    python run.py 9000       # 指定端口
"""

import asyncio
import sys

# Windows 上必须用 SelectorEventLoop
# ProactorEventLoop 会导致子线程中 translate_stream 报 [Errno 22]
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8377
    print(f"\n  🌐 LingoPDF 已启动: http://127.0.0.1:{port}\n")
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="warning")