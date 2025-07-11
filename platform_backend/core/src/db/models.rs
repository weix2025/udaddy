// 数据库模型定义：定义所有与数据库表对应的Rust struct。
// 包括：User, AssetFile, Agent, Pipeline, PipelineStep, Run, RunOutput, RunDerivativeData。
// 所有模型都派生sqlx::FromRow和serde::{Serialize, Deserialize}。
// 这里将明确定义实体间的关系，例如Run与RunOutput之间的一对多关系。