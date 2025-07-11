// 统一错误处理：定义平台统一的Error枚举和Result<T, Error>类型。
// 它将sqlx::Error, std::io::Error, reqwest::Error等底层错误统一封装，
// 并为axum实现IntoResponse Trait，使得在API处理器中可以直接通过?操作符传播错误，
// 并自动转换为合适的HTTP错误响应（如404, 500）。