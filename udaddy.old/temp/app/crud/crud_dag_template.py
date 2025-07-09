from app.crud.base import CRUDBase
from app.models.dag_template import DAGTemplate
from app.schemas.dag_template import DAGTemplateCreate, DAGTemplateUpdate

class CRUDDAGTemplate(CRUDBase[DAGTemplate, DAGTemplateCreate, DAGTemplateUpdate]):
    pass

dag_template = CRUDDAGTemplate(DAGTemplate)