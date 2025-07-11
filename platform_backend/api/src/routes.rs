// 路由聚合：定义顶层的axum::Router，
// 将所有业务模块的路由（用户、资产、AI编排等）通过nest()或merge()方法组合到一起，
// 形成清晰的API路径结构，如/api/v1/users, /api/v1/pipelines。