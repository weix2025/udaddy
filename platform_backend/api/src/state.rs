// 应用状态：定义AppState结构体，
// 包含sqlx::PgPool数据库连接池、Arc<AIPlanner> AI规划器实例等所有需要跨请求共享的状态。
// 使用Arc来实现线程安全的共享。