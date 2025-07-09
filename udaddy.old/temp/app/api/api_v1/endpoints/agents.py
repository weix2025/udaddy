# app/api/api_v1/endpoints/agents.py

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.db import base as models

router = APIRouter()

@router.post("/", response_model=schemas.AgentInDB)
def create_agent(
    *,
    db: Session = Depends(deps.get_db),
    agent_in: schemas.AgentCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    创建一个新的Agent。
    Agent的所有权会赋予当前登录的用户。
    """
    agent = crud.agent.create_with_owner(db=db, obj_in=agent_in, owner_id=current_user.id)
    return agent

@router.get("/", response_model=List[schemas.AgentInDB])
def read_agents(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取Agent列表。
    （可以扩展为只获取当前用户拥有的Agent）
    """
    agents = crud.agent.get_multi(db, skip=skip, limit=limit)
    return agents

@router.get("/{agent_id}", response_model=schemas.AgentInDB)
def read_agent(
    *,
    db: Session = Depends(deps.get_db),
    agent_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    根据ID获取指定的Agent。
    """
    agent = crud.agent.get(db=db, id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent未找到")
    # 可以在这里添加权限检查，确保用户只能访问自己的Agent
    # if agent.owner_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="没有权限")
    return agent