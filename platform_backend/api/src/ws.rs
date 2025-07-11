// WebSocket模块：管理与前端的WebSocket连接，
// 如GET /ws/runs/{run_id}/subscribe。
// 当连接建立后，api服务会订阅Redis中与该run_id相关的频道，
// 并将worker发布的状态更新、日志流等信息实时地转发给前端。