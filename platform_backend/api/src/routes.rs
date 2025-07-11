use axum::{Router, routing::{get, post}, middleware};
use crate::{
    state::AppState,
    handlers,
    middleware::auth_middleware,
};

pub fn create_router(app_state: AppState) -> Router {
    let api_routes = Router::new()
        .route("/orchestrator/suggest-pipelines", post(handlers::orchestrator::suggest_pipelines))
        .route("/pipelines", post(handlers::pipelines::create_pipeline))
        .route("/agents", post(handlers::agents::create_agent))
        .route("/runs", post(handlers::runs::start_run))
        .route("/assets/upload-url", post(handlers::assets::get_upload_url))
        .layer(middleware::from_fn_with_state(app_state.clone(), auth_middleware));

    Router::new()
        .nest("/api/v1", api_routes)
        .route("/ws/runs/:run_id/subscribe", get(handlers::ws::websocket_handler))
        .with_state(app_state)
}