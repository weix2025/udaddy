use axum::{Router, Server};
use std::net::SocketAddr;
use tower_http::cors::CorsLayer;
use core::db;
use crate::state::AppState;
use crate::routes::create_router;

mod handlers;
mod middleware;
mod routes;
mod state;
mod view_models;
mod ws;

#[tokio::main]
async fn main() -> core::error::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let db_pool = db::init_db_pool().await?;
    let app_state = AppState::new(db_pool);

    let app = create_router(app_state).layer(CorsLayer::permissive());

    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    tracing::info!("listening on {}", addr);

    Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();

    Ok(())
}