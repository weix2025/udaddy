# app/schemas/agent.py

from pydantic import BaseModel, Field
from typing import Dict, Any
from app.db.base import AgentType

# Pydantic模型，用于API的数据验证和序列化

class AgentBase(BaseModel):
    """Agent的基础模型，包含通用字段"""
    name: str = Field(..., description="Agent的唯一名称，应具有描述性。")
    description: str | None = Field(None, description="对Agent功能的详细描述。")
    agent_type: AgentType = Field(..., description="Agent的实现类型 (DOCKER, WASM, etc.)")
    source_reference: str = Field(..., description="执行源引用（如Docker镜像名, Wasm文件路径）")
    input_schema: Dict[str, Any] | None = Field({}, description="输入参数的JSON Schema定义, 用于自动生成UI和校验。")
    output_schema: Dict[str, Any] | None = Field({}, description="输出结果的JSON Schema定义。")

class AgentCreate(AgentBase):
    """创建Agent时使用的模型"""
    pass

class AgentUpdate(AgentBase):
    """更新Agent时使用的模型"""
    pass

class AgentInDB(AgentBase):
    """从数据库读取Agent数据时使用的模型"""
    id: int
    owner_id: int

    # orm_mode = True 告诉Pydantic模型从ORM对象（如SQLAlchemy模型）中读取数据
    class Config:
        orm_mode = True