# app/api/api_v1/endpoints/workflows.py

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.db import base as models
from app.managers.workflow_manager import workflow_manager # 导入业务逻辑管理器

router = APIRouter()

# --- DAG Template Endpoints ---

@router.post("/templates/", response_model=schemas.DAGTemplateInDB)
def create_dag_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: schemas.DAGTemplateCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    创建一个新的工作流模板 (DAGTemplate)。
    """
    # 这里我们直接调用manager来处理业务逻辑
    template = workflow_manager.create_template(db=db, obj_in=template_in, owner_id=current_user.id)
    return template

@router.get("/templates/{template_id}", response_model=schemas.DAGTemplateInDB)
def read_dag_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取指定ID的工作流模板详情。
    """
    template = workflow_manager.get_template(db=db, template_id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板未找到")
    # 权限检查
    if template.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限访问此模板")
    return template

# --- Workflow Instance Endpoints ---

@router.post("/instances/", response_model=schemas.WorkflowInstanceCreateResponse)
def run_workflow(
    *,
    db: Session = Depends(deps.get_db),
    instance_in: schemas.WorkflowInstanceCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    根据模板和输入参数，触发一个新的工作流实例。
    这是一个异步操作的起点。
    """
    # 1. 获取模板
    template = workflow_manager.get_template(db=db, template_id=instance_in.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="要使用的工作流模板未找到")
    
    # 2. 创建工作流实例记录
    instance = workflow_manager.create_instance(
        db=db,
        template=template,
        instance_in=instance_in,
        owner_id=current_user.id
    )
    
    # 3. 触发工作流开始事件（发送到调度器）
    workflow_manager.trigger_workflow_start(instance)
    
    return {"instance_id": instance.id, "status": instance.status.value}


@router.get("/instances/{instance_id}", response_model=schemas.WorkflowInstanceInfo)
def get_workflow_instance_status(
    *,
    db: Session = Depends(deps.get_db),
    instance_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取指定工作流实例的当前状态和详情。
    """
    instance = crud.workflow_instance.get(db, id=instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="工作流实例未找到")
    
    # 权限检查
    if instance.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限访问此实例")
        
    return instance