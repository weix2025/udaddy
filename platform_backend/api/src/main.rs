// 服务器入口：初始化Tokio运行时、加载配置、创建应用状态AppState、
// 组合所有路由并启动axum服务器。
// 这里还会配置日志、CORS策略、以及优雅停机（graceful shutdown）逻辑。

fn main() {
    println!("Hello, from api!");
}