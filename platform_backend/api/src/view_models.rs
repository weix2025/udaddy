use serde::{Serialize, Deserialize};
use validator::Validate;

#[derive(Validate, Deserialize)]
pub struct UserSignup {
    #[validate(length(min = 1, max = 50))]
    pub username: String,
    #[validate(length(min = 8))]
    pub password: String,
}

#[derive(Serialize)]
pub struct UserView {
    pub id: String,
    pub username: String,
}

// TODO: Add other view models for Agent, Pipeline, Run, etc.