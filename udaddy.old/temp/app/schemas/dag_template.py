# app/schemas/dag_template.py
from pydantic import BaseModel, Field
from typing import Dict, Any, List

class DAGTemplateBase(BaseModel):
    """DAG模板的基础模型"""
    name: str = Field(..., description="模板的名称，应具有描述性。")
    description: str | None = Field(None, description="对模板功能的详细描述。")
    dag_definition: Dict[str, List[Dict[str, Any]]] = Field(
        ...,
        description=(
            "核心DAG结构定义。包含'nodes'和'edges'两个键。"
            "每个node应包含'id'(唯一标识), 'agent_id'。"
            "每个edge应包含'from'(源节点id), 'to'(目标节点id)。"
            "Node内可包含高级策略，如 'retry_policy': {'max_retries': 3}, 'timeout_seconds': 600"
        ),
        example={
            "nodes": [
                {"id": "start", "agent_id": 1, "timeout_seconds": 300},
                {"id": "process", "agent_id": 2, "retry_policy": {"max_retries": 2, "delay_seconds": 30}},
                {"id": "end", "agent_id": 3}
            ],
            "edges": [
                {"from": "start", "to": "process"},
                {"from": "process", "to": "end"}
            ]
        }
    )

class DAGTemplateCreate(DAGTemplateBase):
    """创建DAG模板时使用的模型"""
    pass

class DAGTemplateUpdate(DAGTemplateBase):
    """更新DAG模板时使用的模型"""
    pass

class DAGTemplateInDB(DAGTemplateBase):
    """从数据库读取DAG模板数据时使用的模型"""
    id: int
    owner_id: int

    class Config:
        orm_mode = True