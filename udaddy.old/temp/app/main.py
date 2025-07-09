# app/main.py
from fastapi import FastAPI
from app.api.api_v1.api import api_router  # 导入修正后的主路由
from app.core.config import settings

# 创建FastAPI应用实例，并添加我们之前设计好的详细文档信息
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="一个可组合、可扩展的AI工作流引擎平台。允许您通过DAG定义、执行和监控复杂的AI任务流。",
    version="1.0.0",
)

# 将 v1 版本的API路由挂载到 /api/v1 前缀下
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", summary="健康检查")
def read_root():
    """
    根路径，可以用于服务的健康检查。
    """
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}