use serde::{Serialize, Deserialize};
use sqlx::{FromRow, types::chrono::{DateTime, Utc}};
use uuid::Uuid;

#[derive(Debug, FromRow, Serialize, Deserialize)]
pub struct User {
    pub id: Uuid,
    pub username: String,
    pub password_hash: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct NewUser {
    pub username: String,
    pub password_hash: String,
}

#[derive(Debug, FromRow, Serialize, Deserialize)]
pub struct AssetFile {
    pub id: Uuid,
    pub user_id: Uuid,
    pub file_name: String,
    pub s3_path: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, FromRow, Serialize, Deserialize, Clone, PartialEq)]
pub struct Agent {
    pub id: Uuid,
    pub name: String,
    pub description: String,
    pub wasm_asset_id: Uuid,
    pub capabilities: serde_json::Value, // JSONB
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, FromRow, Serialize, Deserialize)]
pub struct Pipeline {
    pub id: Uuid,
    pub name: String,
    pub description: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, FromRow, Serialize, Deserialize)]
pub struct PipelineStep {
    pub id: Uuid,
    pub pipeline_id: Uuid,
    pub agent_id: Uuid,
    pub step_order: i32,
}

#[derive(Debug, FromRow, Serialize, Deserialize)]
pub struct Run {
    pub id: Uuid,
    pub pipeline_id: Option<Uuid>,
    pub agent_id: Option<Uuid>,
    pub status: String,
    pub created_at: DateTime<Utc>,
    pub finished_at: Option<DateTime<Utc>>,
}

#[derive(Debug, FromRow, Serialize, Deserialize)]
pub struct RunOutput {
    pub id: Uuid,
    pub run_id: Uuid,
    pub asset_id: Uuid,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, FromRow, Serialize, Deserialize)]
pub struct RunDerivativeData {
    pub id: Uuid,
    pub run_id: Uuid,
    pub data: serde_json::Value, // JSONB
    pub created_at: DateTime<Utc>,
}