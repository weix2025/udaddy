use argon2::{Argon2, PasswordHash, PasswordHasher, PasswordVerifier};
use argon2::password_hash::SaltString;
use rand_core::OsRng;
use jwt::{Header, Token, claims::Claims as JwtClaims, algorithm::AlgorithmType};
use jwt::SignWithKey;
use jwt::VerifyWithKey;
use hmac::{Hmac, Mac};
use sha2::Sha256;
use chrono::{Utc, Duration};
use serde::{Serialize, Deserialize};
use crate::error::{Result, Error};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Claims {
    pub sub: String,
    pub exp: i64,
}

pub async fn hash_password(password: String) -> Result<String> {
    tokio::task::spawn_blocking(move || {
        let salt = SaltString::generate(&mut OsRng);
        let argon2 = Argon2::default();
        let password_hash = argon2.hash_password(password.as_bytes(), &salt)
            .map_err(|e| Error::Argon2(e.to_string()))?
            .to_string();
        Ok(password_hash)
    }).await.unwrap()
}

pub async fn verify_password(hash: &str, password: &str) -> Result<bool> {
    let parsed_hash = PasswordHash::new(hash).map_err(|e| Error::Argon2(e.to_string()))?;
    let argon2 = Argon2::default();
    Ok(argon2.verify_password(password.as_bytes(), &parsed_hash).is_ok())
}

pub fn generate_jwt(user_id: &str, secret: &str) -> Result<String> {
    let header: Header = Default::default();
    let now = Utc::now();
    let expiration = now + Duration::days(7);

    let claims = Claims {
        sub: user_id.to_string(),
        exp: expiration.timestamp(),
    };
    
    let key: Hmac<Sha256> = Hmac::new_from_slice(secret.as_bytes()).unwrap();
    let token = Token::new(header, claims).sign_with_key(&key).map_err(Error::Jwt)?;

    Ok(token.as_str().to_string())
}

pub fn decode_jwt(token_str: &str, secret: &str) -> Result<Claims> {
    let key: Hmac<Sha256> = Hmac::new_from_slice(secret.as_bytes()).unwrap();
    let token: Token<Header, Claims, _> = Token::parse_unverified(token_str).map_err(Error::Jwt)?;
    let claims = token.verify_with_key(&key).map_err(Error::Jwt)?;
    
    Ok(claims.claims().clone())
}