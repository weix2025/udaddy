Netbase架构升级与集成方案 (详细版)
本方案旨在将现有代码库与《Netbase平台架构设计备忘录 (V1)》中定义的新架构进行整合。我们将分五个阶段进行，确保每一步都清晰、可控、且与最终目标高度一致。

阶段一：数据库模型升级 (奠定“版本化资产”的基石)
这是所有后续工作的基础，也是从“任务执行”思维转向“资产管理”思维的根本转变。我们将重构数据模型，从简单的Agent模型升级为支持版本控制、逻辑分组和全生命周期管理的“版本化资产包”模型。

目标: 完整实现备忘录 2.2. 版本化的资产包管理 所定义的数据库结构。

行动计划:

新增数据模型: 在 app/db/base.py (或为保持清晰性，在新建的 app/models/asset.py 文件) 中，创建三个新的、关系明确的SQLModel模型：

AssetPackage: 资产的顶层逻辑容器。

id (PK), nanoid (用于API交互的全局唯一ID), name (用户指定的、易于记忆的唯一名称), owner_id (外键，关联到用户表，用于权限控制)。

AssetVersion: 资产包的版本快照。

id (PK), package_id (外键，指明归属的资产包), version_string (遵循语义化版本，如 "1.0.0", "1.1.0-beta"), description (文本字段，描述此版本的变更内容), created_at。

AssetFile:构成一个版本的具体文件。

id (PK), version_id (外键，指明归属的版本), file_type (枚举类型，如 WASM, CONFIG_JSON, SQL_SCRIPT, DOCKERFILE, README_MD), relative_path (相对于版本目录的路径，如 "bin/processor.wasm"), checksum (SHA256哈希，用于校验文件完整性，防止篡改)。

重构 Agent 模型: 修改 app/db/base.py 中的 Agent 模型，使其成为一个“可执行指针”。

移除 source_reference 字段，其功能被新的资产模型完全取代。

新增 asset_file_id 字段，并将其设置为指向 asset_files.id 的外键。这建立了Agent与一个精确、版本化的物理文件之间的直接链接。

config 字段的用途现在转变为“执行时覆盖参数”，允许同一个资产文件在不同的Agent定义下以不同的默认参数运行。

创建CRUD操作: 为新增的三个模型创建对应的CRUD文件（如 app/crud/crud_asset_package.py）。这些不仅仅是简单的增删改查，还需要包含一些关键的业务逻辑，例如：

crud_asset_package.create 需要确保 name 和 nanoid 的唯一性。

crud_asset_version.create 需要在一个数据库事务中同时创建版本记录和其下所有文件的记录。

数据库迁移:

生成脚本: 运行 alembic revision --autogenerate -m "add asset management models" 来生成一个新的数据库迁移脚本。

仔细审查: 这是至关重要的一步。需要仔细检查生成的脚本，确保它正确地创建了新表、添加了外键约束，并正确地修改了agents表。对于现有agents表中的数据，可能需要编写一个数据迁移逻辑，为它们创建默认的资产包和版本，以保证向后兼容。

应用迁移: 在确认无误后，运行 alembic upgrade head 应用迁移。

结果: 完成后，我们的数据库将从一个简单的平面结构，进化为一个能够支撑企业级功能（如版本控制、审计追溯、依赖管理）的、结构化的资产库。这是平台走向成熟的坚实第一步。

阶段二：API层扩展 (开放资产管理能力)
目标: 实现备忘录 2.2. 生命周期管理 中描述的API，为用户和外部系统提供管理版本化资产的编程接口。

行动计划:

创建新的API端点文件: 新建 app/api/api_v1/endpoints/asset_packages.py，专门用于处理所有与资产包相关的交互。

实现API: 在新文件中，实现以下核心端点，并为其配备详细的Pydantic模型进行输入验证和输出序列化：

POST /asset-packages: 创建一个新的资产包。请求体: { "name": "my-image-processor" }。响应体: { "id": 1, "nanoid": "aV1_iF4gT-7b", "name": "my-image-processor" }。

POST /asset-packages/{nanoid}/versions: 为指定的资产包发布一个新版本。这是一个复杂的端点，需要处理 multipart/form-data 请求。请求中应包含元数据（如 version_string: "1.0.0"）和实际的文件内容。后端逻辑需要原子性地完成文件保存、校验和计算、以及数据库记录的创建。

GET /asset-packages: 列出所有资产包，支持分页和按名称搜索。

GET /asset-packages/{nanoid}/versions: 列出特定资产包的所有版本。

修改Agent端点: 大幅修改 app/api/api_v1/endpoints/agents.py。

创建Agent的请求体 AgentCreate 现在需要接收 asset_file_id: int 和 name: str，而不再是上传文件或提供源码。这强制将Agent的定义与其所依赖的、版本化的资产文件解耦。

需要提供辅助API，例如 GET /asset-packages/{nanoid}/{version}/files，以便前端UI可以构建一个文件选择器，让用户在创建Agent时能方便地选择要引用的资产文件。

结果: 我们的平台现在拥有了通过API进行程序化资产管理的完整能力。这不仅支持了UI操作，也为未来实现CI/CD集成（例如，通过GitLab CI自动发布新版本的WASM模块）奠定了基础。

阶段三：调度器重构 (从“单任务”到“任务组”)
这是后台逻辑的第一次重大变革。我们将彻底修改 scheduler.py 的核心分发逻辑，使其从“逐一分发”的微观管理者，转变为“批量打包”的宏观调度中心。

目标: 实现备忘录 3.1. 调度器，提升调度效率和系统的可观测性。

行动计划:

修改 handle_scheduler_event:

当START_WORKFLOW事件触发时，在找到所有入度为0的起始节点后，不再是循环调用create_and_dispatch_task_instance。而是将这些节点打包成一个列表，统一调用一个新的核心函数 dispatch_task_group。

当TASK_COMPLETED事件触发时，在找到所有新就绪的下游节点后，同样将它们打包成一个待分发列表，调用 dispatch_task_group。这种批处理方式能显著减少数据库和消息队列的交互次数。

创建 dispatch_task_group 函数:

此函数接收一个节点定义列表，是新的调度核心。

生成group_id: 使用 nanoid 库为本次分发的所有任务生成一个唯一的group_id。这个ID将作为日志追踪和事务管理的关键。

构建载荷: 在一个数据库事务中，遍历节点列表，为每个节点：

创建TaskInstance数据库记录，并立即将其状态置为PENDING。

构建绝对路径: 这是关键一步。通过agent_id -> agents.asset_file_id -> asset_files -> asset_versions -> asset_packages 的一整套关联查询，动态地、准确地拼装出WASM模块的绝对物理路径（如 /var/lib/netbase/modules/aV1_iF4gT-7b/1.0.0/bin/processor.wasm）。

将任务执行所需的所有信息（包括task_instance_id, agent_type, 模块的绝对路径, 输入参数等）组装成一个字典。

发送任务: 将包含group_id和任务字典列表的最终载荷，通过 celery_app.send_task 发送给一个新的、统一的Celery任务入口：netbase.worker.execute_group。

移除旧代码: create_and_dispatch_task_instance 函数的功能已被完全取代，可以安全地移除或标记为废弃。

结果: 调度器不再是逐个派单的“调度员”，而是一个高效的“集装箱装箱员”，将一批批的任务高效地打包并发送到执行港口。这大大提升了系统的吞吐量和健壮性。

阶段四：Worker彻底改造 (拥抱异步并发)
这是最大、最核心的一次重构。我们将用一个基于asyncio的、现代化的、高性能的异步并发模型，彻底替换现有的同步worker.py。

目标: 实现备忘录 3.2. 异步Worker，将系统性能提升一个数量级。

行动计划:

重写 worker.py:

移除旧的、同步的 run_agent_task。

创建新的Celery任务入口 execute_group(payload: dict)。这个函数本身是同步的，作为进入异步世界的桥梁。

在execute_group内部，使用 asyncio.run() 调用一个新的异步主函数 run_async_task_group，将接收到的载荷传递进去。

实现 run_async_task_group:

此函数是新的执行核心，它接收group_id和任务列表。

批量状态更新: 在函数开头，通过一次数据库查询，将任务组内所有任务的状态批量更新为RUNNING。

并发执行: 使用 asyncio.TaskGroup 并发地为任务列表中的每个任务创建一个协程。根据任务的agent_type，调用不同的、专门的异步执行函数（如run_wasm_calculation, run_docker_container）。

结果处理: TaskGroup执行结束后（即组内所有任务都已完成），收集所有协程的返回结果。

批量状态更新: 根据返回结果，再次批量更新数据库中任务的状态（COMPLETED/FAILED）和输出。

事件提交通知: 为每个完成的任务，向调度器提交TASK_COMPLETED或TASK_FAILED事件，触发工作流的下一步。

结果: 我们的Worker从一个一次只能做一件事的“手工作坊”，升级为了一个能同时处理成百上千个并发请求的“现代化智能工厂”，系统的响应能力和处理能力得到质的飞跃。

阶段五：WASM执行器落地 (集成安全沙箱)
最后，我们将实现平台安全的核心——WASM执行能力，将我们精心设计的WasmManager集成到新的异步Worker中。

目标: 实现备忘录 4.1. WasmManager执行器 和 4.2. 数据交换与工作区，完成从蓝图到现实的最后一公里。

行动计划:

创建 app/tasks/wasm_manager.py:

将备忘录中设计的WasmManager生产环境完整版代码放入此文件。

确保其中完整实现了Fuel限制、WASI沙箱配置（特别是preopen_dir）、模块缓存和我们自定义的内存投递协议。

在 worker.py 中集成:

在模块顶部，创建一个WasmManager的全局单例，它将在Worker进程的生命周期内被复用。

创建 run_wasm_calculation 异步函数，它将作为TaskGroup中的一个协程任务被调用。

实现工作区逻辑: 这是文件处理安全的关键。

在此函数中，调用WasmManager.execute之前，为每个WASM任务创建一个唯一的、基于group_id和task_instance_id的临时工作区目录。

负责将任务需要的输入文件（例如从S3下载或从本地拷贝）准备到工作区中。

调用WasmManager.execute，并将这个安全的工作区路径作为workspace_dir参数传入。

在finally块中，必须确保无论任务成功与否，这个临时工作区目录及其所有内容都被彻底删除，防止磁盘空间泄漏。

将WasmManager返回的结果（包含status和output/error）进行处理，并作为协程的最终结果返回。

结果: 我们的平台现在拥有了执行用户代码和第三方模块的核心安全能力。通过一个结合了资源限制、权限隔离和临时文件系统的纵深防御体系，我们能够自信地运行不可信的计算任务，为平台的未来功能扩展（如在线代码编辑器、自定义AI模型执行）提供了无限可能。