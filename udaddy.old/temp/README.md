# Netbase - 版本化资产管理与安全计算平台

Netbase 正在经历一次深刻的架构演进，从一个传统的AI工作流引擎，升级为一个以“**版本化数字资产**”为核心的、健壮的、可扩展的安全计算平台。

> **重要提示:** 本项目正处于重大架构重构中。我们已经完成了后端核心执行引擎的现代化改造。当前的工作焦点是实现全新的“版本化资产管理”数据模型和API。完整的技术细节、设计决策和演进路线图，请参阅 **[dashboard.xml](./dashboard.xml)**。

## ✨ 核心理念与特性

*   **版本化资产包**: 我们不再管理零散的Agent，而是管理版本化的“资产包”。每个资产包是一个逻辑项目，可以包含多个版本，每个版本可以包含多种文件（如WASM模块, SQL脚本, 配置文件等）。
*   **Agent即指针**: Agent不再是实体，而是一个指向“资产包”中某个特定版本、特定文件的**“可执行指针”**。它定义了“如何运行这个资产”，实现了定义与实体的彻底解耦。
*   **高性能与高并发**: 基于FastAPI和Celery，采用异步I/O和批量任务组调度，充分利用系统资源。
*   **安全沙箱**: 所有WASM模块都在一个资源受限（Fuel/超时）、文件系统隔离的安全沙箱中执行，确保了平台的安全性。
*   **DAG驱动**: 通过JSON灵活定义复杂任务依赖和执行流程。
*   **开发者友好**: 提供自动化的API文档和简化的本地部署方案。

## 🏛️ 全新架构

平台的核心业务被拆分为四个互相协作的模块：

1.  **资产管理 (Asset Management)**: 负责所有“可执行单元”的创建、版本控制、存储和元数据管理。
2.  **工作流定义 (Workflow Definition)**: 负责业务流程的编排，定义任务节点之间的依赖关系。
3.  **智能调度 (Intelligent Scheduler)**: 平台的大脑。负责解析工作流，并将任务高效地批量分发给执行单元。
4.  **安全执行 (Secure Worker)**: 平台的手脚。在隔离的、资源受限的环境中安全地执行具体任务。

## 🚀 快速开始 (本地开发)

请按照以下步骤在您的本地机器上启动整个Netbase平台。

### 1. 先决条件

*   [Git](https://git-scm.com/)
*   [Python](https://www.python.org/downloads/) 3.10+
*   [Docker](https://www.docker.com/products/docker-desktop/) 和 Docker Compose

### 2. 克隆与安装

```bash
# 1. 克隆项目仓库
git clone https://github.com/your-username/netbase-code.git
cd netbase-code

# 2. 创建并激活Python虚拟环境
python -m venv venv
# 在 Windows 上: venv\Scripts\activate
# 在 MacOS/Linux 上: source venv/bin/activate

# 3. 安装所有Python依赖
pip install -r requirements.txt
```

### 3. 环境配置

```bash
# 1. 启动后台服务 (PostgreSQL 和 Redis)
docker-compose up -d

# 2. 如果.env文件不存在，从.env.example复制
if [ ! -f .env ]; then cp .env.example .env; fi

# 3. !!! 重要: 检查 .env 文件 !!!
#    - 确保 SECRET_KEY 已设置。
#    - 确认数据库和Redis的连接信息与 docker-compose.yml 中一致。
```

### 4. 数据库迁移

我们使用 Alembic 来管理数据库结构变更。

```bash
# 应用所有迁移到数据库
alembic upgrade head
```
**注意:** 当 `dashboard.xml` 中定义的数据库模型变更被实现后，需要运行 `alembic revision --autogenerate -m "Implement asset management models"` 来生成新的迁移脚本。

### 5. 启动应用

现在，打开2个独立的终端窗口，分别启动核心服务。

**终端 1: 启动 FastAPI API 服务器**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
启动后，访问 `http://localhost:8000/docs` 查看自动生成的API文档。

**终端 2: 启动Celery Worker集群**
(我们的新架构简化了Worker的分类，所有Worker都从同一个队列消费)
```bash
celery -A app.tasks.celery_app worker --loglevel=info -Q compute_queue -n worker@%h
```

🎉 恭喜！Netbase平台现在已经在您的本地机器上运行起来了。
