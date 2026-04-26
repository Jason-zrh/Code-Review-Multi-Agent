from fastapi import FastAPI
from src.api.routes import router
from config.settings import settings


# ============================================================
# 应用入口
# 作用：创建 FastAPI 应用，注册路由
# 访问 /docs 查看自动生成的 API 文档
# ============================================================

app = FastAPI(
    title="Code Review Multi-Agent",
    description="AI-powered code review system with Multi-Agent architecture",
    version="0.1.0",
)

# 注册路由（在 routes.py 中定义）
app.include_router(router)


@app.get("/health")
def health_check():
    """健康检查端点

    用于：负载均衡探活、部署验证
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
