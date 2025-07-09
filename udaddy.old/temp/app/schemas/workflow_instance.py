# app/schemas/workflow_instance.py
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime
from app.db.base import WorkflowStatus, TaskStatus # 从模型中导入状态定义

class WorkflowInstanceCreate(BaseModel):
    """用于触发新工作流实例的请求体"""
    template_id: int = Field(
        ...,
        description="要使用的工作流模板（DAGTemplate）的唯一ID。",
        example=123
    )
    inputs: Dict[str, Any] = Field(
        ...,
        description=(
            "一个键值对字典，提供本次运行所需的初始输入参数。"
            "这些输入的键（key）必须与DAG模板中起始节点所需的输入相对应。"
        ),
        example={"image_url": "http://example.com/image.jpg", "strength": 0.8}
    )
    priority: int = Field(
        0,
        description="工作流的执行优先级，数字越大优先级越高。默认为0。",
        example=10
    )

class WorkflowInstanceCreateResponse(BaseModel):
    """成功触发工作流后的响应体"""
    instance_id: int = Field(..., description="新创建的工作流实例的唯一ID，可用于后续状态查询。")
    status: str = Field(..., description="工作流实例的初始状态，通常是'QUEUED'。")

class TaskInstanceInfo(BaseModel):
    """用于在响应中展示的单个任务实例的摘要信息"""
    id: int
    node_id_in_dag: str
    status: TaskStatus
    started_at: datetime | None
    completed_at: datetime | None

    class Config:
        orm_mode = True

class WorkflowInstanceInfo(BaseModel):
    """获取工作流实例详细信息时的响应模型"""
    id: int
    template_id: int
    status: WorkflowStatus
    priority: int
    inputs: Dict[str, Any]
    outputs: Dict[str, Any] | None
    owner_id: int
    started_at: datetime | None
    completed_at: datetime | None
    task_instances: List[TaskInstanceInfo]

    class Config:
        orm_mode = True