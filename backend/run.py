#!/usr/bin/env python3
"""
后端服务启动脚本
用于开发环境快速启动 FastAPI 服务
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发环境启用热重载
        log_level="info",
    )
