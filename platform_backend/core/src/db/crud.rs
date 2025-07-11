use sqlx::PgPool;
use uuid::Uuid;
use super::models::{User, NewUser};
use crate::error::Result;
// User CRUD
pub async fn create_user(pool: &PgPool, new_user: NewUser) -> Result<User> {
    let user = sqlx::query_as::<_, User>("INSERT INTO users (username, password_hash) VALUES ($1, $2) RETURNING *")
        .bind(new_user.username)
        .bind(new_user.password_hash)
        .fetch_one(pool)
        .await?;
    Ok(user)
}

pub async fn get_user_by_username(pool: &PgPool, username: &str) -> Result<Option<User>> {
    let user = sqlx::query_as::<_, User>("SELECT * FROM users WHERE username = $1")
        .bind(username)
        .fetch_optional(pool)
        .await?;
    Ok(user)
}

pub async fn get_user_by_id(pool: &PgPool, user_id: Uuid) -> Result<Option<User>> {
    let user = sqlx::query_as::<_, User>("SELECT * FROM users WHERE id = $1")
        .bind(user_id)
        .fetch_optional(pool)
        .await?;
    Ok(user)
}

// TODO: Implement CRUD for other models (AssetFile, Agent, Pipeline, etc.)