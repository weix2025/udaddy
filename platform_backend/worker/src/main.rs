mod consumer;
mod processor;

use core::db;
use tracing::info;

#[tokio::main]
async fn main() -> core::error::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    info!("Starting worker");

    let db_pool = db::init_db_pool().await?;
    
    // TODO: Initialize Redis client

    // TODO: Start consumer loop

    Ok(())
}