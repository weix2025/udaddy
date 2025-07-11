use axum::{
    http::{Request, StatusCode},
    middleware::Next,
    response::Response,
};
use crate::state::AppState;
use core::security::decode_jwt;

pub async fn auth_middleware<B>(
    mut req: Request<B>,
    next: Next<B>,
    state: AppState,
) -> Result<Response, StatusCode> {
    let auth_header = req.headers()
        .get("Authorization")
        .and_then(|header| header.to_str().ok());

    if let Some(auth_header) = auth_header {
        if let Some(token) = auth_header.strip_prefix("Bearer ") {
            if let Ok(claims) = decode_jwt(token, &state.jwt_secret) {
                // Add user_id to request extensions
                req.extensions_mut().insert(claims.sub);
                return Ok(next.run(req).await);
            }
        }
    }

    Err(StatusCode::UNAUTHORIZED)
}