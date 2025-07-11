use serde::Deserialize;
use once_cell::sync::Lazy;
use std::env;

#[derive(Deserialize, Debug)]
pub struct Config {
    pub database_url: String,
    pub jwt_secret: String,
    pub minio_endpoint: String,
}

pub static CONFIG: Lazy<Config> = Lazy::new(|| {
    dotenvy::dotenv().ok();
    Config {
        database_url: env::var("DATABASE_URL").expect("DATABASE_URL must be set"),
        jwt_secret: env::var("JWT_SECRET").expect("JWT_SECRET must be set"),
        minio_endpoint: env::var("MINIO_ENDPOINT").expect("MINIO_ENDPOINT must be set"),
    }
});