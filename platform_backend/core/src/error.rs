use thiserror::Error;

pub type Result<T> = std::result::Result<T, Error>;

#[derive(Debug, Error)]
pub enum Error {
    #[error("Database error: {0}")]
    Sqlx(#[from] sqlx::Error),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("JWT error: {0}")]
    Jwt(#[from] jwt::Error),

    #[error("Argon2 error: {0}")]
    Argon2(String),

    #[error("Wasmtime error: {0}")]
    Wasmtime(#[from] wasmtime::Error),

    #[error("Wasm memory error: {0}")]
    WasmMemory(String),
    
    #[error("Config error: {0}")]
    Config(#[from] std::env::VarError),
}

impl From<argon2::Error> for Error {
    fn from(err: argon2::Error) -> Self {
        Error::Argon2(err.to_string())
    }
}
