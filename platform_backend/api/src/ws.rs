use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        State,
        Path,
    },
    response::IntoResponse,
};
use crate::state::AppState;
use uuid::Uuid;

pub async fn websocket_handler(
    ws: WebSocketUpgrade,
    State(state): State<AppState>,
    Path(run_id): Path<Uuid>,
) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_socket(socket, state, run_id))
}

async fn handle_socket(mut socket: WebSocket, state: AppState, run_id: Uuid) {
    // TODO: Implement WebSocket logic, including subscribing to Redis pub/sub
    // for the given run_id and forwarding messages.
    
    if socket.send(Message::Text(String::from("Hello, WebSocket!"))).await.is_err() {
        // client disconnected
        return;
    }
}