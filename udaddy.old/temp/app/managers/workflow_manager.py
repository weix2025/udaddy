# app/managers/workflow_manager.py

from sqlalchemy.orm import Session
from app import schemas
from app.db import base as models

def submit_to_scheduler(event: dict):
    """
    一个辅助函数，用于向Celery提交调度事件。
    这是API层和后台任务系统解耦的关键。
    """
    print(f"SCHEDULER EVENT SUBMITTED: {event}")
    # 在实际项目中，这里会导入并调用Celery任务
    from app.tasks.scheduler import handle_scheduler_event
    # 使用apply_async可以指定队列
    handle_scheduler_event.apply_async(args=[event], queue="scheduler_queue")

class WorkflowManager:
    """
    工作流管理器。
    封装了所有与工作流模板和实例相关的核心业务逻辑，
    使API路由层的代码保持干净和专注。
    """
    def get_template(self, db: Session, template_id: int) -> models.DAGTemplate | None:
        """根据ID获取DAG模板"""
        return db.query(models.DAGTemplate).filter(models.DAGTemplate.id == template_id).first()

    def create_template(self, db: Session, *, obj_in: schemas.dag_template.DAGTemplateCreate, owner_id: int) -> models.DAGTemplate:
        """创建一个新的DAG模板"""
        # 将Pydantic schema转换为SQLAlchemy模型实例
        db_obj = models.DAGTemplate(**obj_in.dict(), owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj) # 刷新实例以获取数据库生成的值（如ID）
        return db_obj

    def create_instance(self, db: Session, *, template: models.DAGTemplate, instance_in: schemas.workflow_instance.WorkflowInstanceCreate, owner_id: int) -> models.WorkflowInstance:
        """根据模板和输入参数创建一个新的工作流实例"""
        db_obj = models.WorkflowInstance(
            template_id=template.id,
            owner_id=owner_id,
            inputs=instance_in.inputs,
            priority=instance_in.priority,
            status=models.WorkflowStatus.QUEUED # 初始状态为排队中
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def trigger_workflow_start(self, instance: models.WorkflowInstance):
        """
        向调度器发送“启动工作流”的事件。
        """
        event = {
            "event_type": "START_WORKFLOW",
            "instance_id": instance.id
        }
        submit_to_scheduler(event)

# 创建一个管理器的单例，方便在其他地方直接导入使用
workflow_manager = WorkflowManager()