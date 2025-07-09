# app/api/api_v1/api.py
from fastapi import APIRouter

# 从各个端点模块中导入路由
from .endpoints import login, users, agents, workflows

# 创建一个主API路由器
api_router = APIRouter()

# 将每个子模块的路由包含进来，并可以为它们分配合适的前缀和标签
api_router.include_router(login.router, tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])