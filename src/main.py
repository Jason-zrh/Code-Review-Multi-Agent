from fastapi import FastAPI
from src.api.routes import router
from config.settings import settings


app = FastAPI(
    title="Code Review Multi-Agent",
    description="AI-powered code review system with Multi-Agent architecture",
    version="0.1.0",
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
