from app.crud.base import CRUDBase
from app.models.workflow_instance import WorkflowInstance
from app.schemas.workflow_instance import WorkflowInstanceCreate, WorkflowInstanceUpdate

class CRUDWorkflowInstance(CRUDBase[WorkflowInstance, WorkflowInstanceCreate, WorkflowInstanceUpdate]):
    pass

workflow_instance = CRUDWorkflowInstance(WorkflowInstance)