use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;
use crate::config::CONFIG;
use crate::error::Result;

pub mod crud;
pub mod models;

pub async fn init_db_pool() -> Result<PgPool> {
    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&CONFIG.database_url)
        .await?;
    Ok(pool)
}