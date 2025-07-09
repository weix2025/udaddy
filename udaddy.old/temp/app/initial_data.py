# a new file: app/initial_data.py

import logging

from app.crud import user as crud_user
from app.db.session import SessionLocal
from app.core.config import settings
from app.schemas import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db() -> None:
    db = SessionLocal()
    user = crud_user.user.get_by_username(db, username=settings.FIRST_SUPERUSER)
    if not user:
        logger.info("Creating first superuser")
        
        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            email=settings.FIRST_SUPERUSER_EMAIL,
            is_superuser=True,
        )
        
        user = crud_user.user.create(db, obj_in=user_in)
        logger.info("First superuser created")
    else:
        logger.info("Superuser already exists in database, skipping creation")
    db.close()


if __name__ == "__main__":
    logger.info("Creating initial data")
    init_db()
    logger.info("Initial data created")