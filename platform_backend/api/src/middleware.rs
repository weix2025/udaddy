// 认证中间件：实现JWT认证逻辑。
// 它作为一个axum::middleware，从请求头中提取Authorization bearer token，
// 使用core中的安全工具进行验证，并将解析出的用户ID等信息通过request.extensions_mut()附加到请求中，
// 供下游处理器使用。