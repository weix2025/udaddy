use redis::AsyncCommands;
use crate::processor;
use core::error::Result;

pub async fn start_consumer_loop(
    // redis_client: &mut redis::Client, // TODO: Pass Redis client
    // db_pool: &sqlx::PgPool, // TODO: Pass DB pool
) -> Result<()> {
    // let mut con = redis_client.get_async_connection().await?;
    // let mut pubsub = con.into_pubsub();
    // pubsub.subscribe("task_queue").await?;

    // loop {
    //     let msg = pubsub.get_message().await?;
    //     let payload: String = msg.get_payload()?;
        
    //     // TODO: Deserialize payload and pass to processor
    //     // processor::process_task(db_pool, payload).await?;
    // }
    
    Ok(())
}