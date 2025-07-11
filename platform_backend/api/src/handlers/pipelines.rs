use axum::{extract::State, Json};
use crate::state::AppState;
use core::error::Result;

pub async fn create_pipeline(
    State(state): State<AppState>,
    // Json(payload): Json<...>, // TODO: Define payload
) -> Result<Json<()>> { // TODO: Define response
    // TODO: Implement logic
    Ok(Json(()))
}