# app/db/base.py

import enum
from datetime import datetime

from sqlalchemy import (Column, Integer, String, Boolean, DateTime,
                        ForeignKey, Text, Enum)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB

# 创建一个所有模型都会继承的基类
Base = declarative_base()


# ==============================================================================
# 状态定义 (Enums)
# ==============================================================================

class WorkflowStatus(str, enum.Enum):
    """整个工作流实例的运行状态"""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class TaskStatus(str, enum.Enum):
    """单个任务实例的运行状态"""
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AgentType(str, enum.Enum):
    """AI代理（执行单元）的类型"""
    WASM = "WASM"
    DOCKER = "DOCKER"
    PYTHON_FUNCTION = "PYTHON_FUNCTION"


# ==============================================================================
# 核心数据模型 (Core Data Models)
# ==============================================================================

class User(Base):
    """用户表"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String, unique=True, index=True, comment="邮箱")
    hashed_password = Column(String, nullable=False, comment="哈希加密后的密码")
    full_name = Column(String, index=True, comment="全名")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    is_active = Column(Boolean, default=True, comment="用户是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否为超级用户")

    agents = relationship("Agent", back_populates="owner")
    dag_templates = relationship("DAGTemplate", back_populates="owner")
    workflow_instances = relationship("WorkflowInstance", back_populates="owner")


class Agent(Base):
    """AI代理表"""
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True, comment="Agent的唯一名称")
    description = Column(Text, comment="Agent的功能描述")
    agent_type = Column(Enum(AgentType), nullable=False, comment="Agent的实现类型")
    source_reference = Column(String, nullable=False, comment="执行源引用")
    
    input_schema = Column(JSONB, comment="输入参数的JSON Schema定义")
    output_schema = Column(JSONB, comment="输出结果的JSON Schema定义")

    owner_id = Column(Integer, ForeignKey("users.id"), comment="所属用户的ID")
    owner = relationship("User", back_populates="agents")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DAGTemplate(Base):
    """DAG模板表"""
    __tablename__ = "dag_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, comment="模板名称")
    description = Column(Text, comment="模板功能描述")
    
    dag_definition = Column(JSONB, nullable=False, comment='DAG结构定义 (e.g., {"nodes": [], "edges": []})')

    owner_id = Column(Integer, ForeignKey("users.id"), comment="所属用户的ID")
    owner = relationship("User", back_populates="dag_templates")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    instances = relationship("WorkflowInstance", back_populates="template")


class WorkflowInstance(Base):
    """工作流实例表"""
    __tablename__ = "workflow_instances"
    id = Column(Integer, primary_key=True, index=True)
    
    template_id = Column(Integer, ForeignKey("dag_templates.id"), comment="所使用的模板ID")
    template = relationship("DAGTemplate", back_populates="instances")
    
    status = Column(Enum(WorkflowStatus), nullable=False, default=WorkflowStatus.QUEUED, index=True, comment="工作流当前状态")
    
    priority = Column(Integer, default=0, comment="工作流优先级") # 为优先级调度预留
    
    inputs = Column(JSONB, comment="本次执行的初始输入参数")
    outputs = Column(JSONB, comment="工作流执行完成后的最终输出")
    
    owner_id = Column(Integer, ForeignKey("users.id"), comment="发起此次执行的用户的ID")
    owner = relationship("User", back_populates="workflow_instances")

    started_at = Column(DateTime, comment="执行开始时间")
    completed_at = Column(DateTime, comment="执行结束时间")

    task_instances = relationship("TaskInstance", back_populates="workflow_instance", cascade="all, delete-orphan")


class TaskInstance(Base):
    """任务实例表"""
    __tablename__ = "task_instances"
    id = Column(Integer, primary_key=True, index=True)
    
    workflow_instance_id = Column(Integer, ForeignKey("workflow_instances.id"), nullable=False, comment="所属工作流实例的ID")
    workflow_instance = relationship("WorkflowInstance", back_populates="task_instances")

    node_id_in_dag = Column(String, nullable=False, comment="在DAG定义中的节点ID")

    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, comment="执行此任务所用的Agent ID")
    agent = relationship("Agent")

    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING, index=True, comment="任务当前状态")
    
    inputs = Column(JSONB, comment="任务的实际输入参数")
    outputs = Column(JSONB, comment="任务执行成功后的输出结果")
    logs = Column(Text, comment="任务执行过程中的日志")
    
    retry_count = Column(Integer, default=0, comment="任务失败后的重试次数")
    
    started_at = Column(DateTime, comment="任务开始执行时间")
    completed_at = Column(DateTime, comment="任务执行结束时间")