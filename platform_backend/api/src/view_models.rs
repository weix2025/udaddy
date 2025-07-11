// 视图模型(DTO)：定义专门用于API请求和响应的struct。
// 这层抽象至关重要，它将API的公开契约与内部数据库模型解耦。
// 例如，用户注册的DTOUserSignup会包含password字段，而返回给前端的UserView则绝不会包含它。
// 可利用validator库派生Validate Trait进行请求体验证。