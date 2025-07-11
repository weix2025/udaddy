use sqlx::PgPool;
use std::sync::Arc;
use core::ai::planner::AStarPlanner;

#[derive(Clone)]
pub struct AppState {
    pub db_pool: PgPool,
    pub ai_planner: Arc<AStarPlanner>,
}

impl AppState {
    pub fn new(db_pool: PgPool) -> Self {
        Self {
            db_pool,
            ai_planner: Arc::new(AStarPlanner),
        }
    }
}