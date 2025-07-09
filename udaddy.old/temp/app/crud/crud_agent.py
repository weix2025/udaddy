from typing import List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.db.base import Agent
from app.schemas.agent import AgentCreate, AgentUpdate

class CRUDAgent(CRUDBase[Agent, AgentCreate, AgentUpdate]):
    def create_with_owner(self, db: Session, *, obj_in: AgentCreate, owner_id: int) -> Agent:
        """
        Create a new agent with an owner.
        """
        db_obj = self.model(**obj_in.model_dump(), owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Agent]:
        """
        Get multiple agents by owner ID.
        """
        return (
            db.query(self.model)
            .filter(Agent.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

agent = CRUDAgent(Agent)