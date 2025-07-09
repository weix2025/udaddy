# app/crud/crud_task_instance.py
from app.crud.base import CRUDBase
from app.models.task_instance import TaskInstance
from app.schemas.task_instance import TaskInstanceCreate, TaskInstanceUpdate

class CRUDTaskInstance(CRUDBase[TaskInstance, TaskInstanceCreate, TaskInstanceUpdate]):
    pass

task_instance = CRUDTaskInstance(TaskInstance)