# app/tasks/scheduler.py

import logging
from typing import Dict, Any, List, Set

from sqlalchemy.orm import Session
from nanoid import generate as generate_nanoid

from app import crud, models, schemas
from app.core.config import settings # 导入配置
from app.tasks.celery_app import celery_app # 确保从正确的路径导入
from app.db.session import SessionLocal

# 配置日志记录器
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


# --- DAG 完整性检查 (未改变) ---
# 这部分逻辑对于确保工作流的有效性至关重要，因此予以保留。

def _is_dag_cyclic_util(
    node_id: str,
    adjacency_list: Dict[str, List[str]],
    visited: Set[str],
    recursion_stack: Set[str],
) -> bool:
    """
    使用深度优先搜索（DFS）检测图中是否存在循环的辅助函数。
    """
    visited.add(node_id)
    recursion_stack.add(node_id)

    for neighbour in adjacency_list.get(node_id, []):
        if neighbour not in visited:
            if _is_dag_cyclic_util(
                neighbour, adjacency_list, visited, recursion_stack
            ):
                return True
        elif neighbour in recursion_stack:
            return True

    recursion_stack.remove(node_id)
    return False


def is_dag_cyclic(nodes: List[Dict], edges: List[Dict]) -> bool:
    """
    检查给定的节点和边定义的DAG中是否存在循环。
    """
    adjacency_list = {node["id"]: [] for node in nodes}
    for edge in edges:
        if edge["from"] in adjacency_list and edge["to"] in adjacency_list:
            adjacency_list[edge["from"]].append(edge["to"])

    visited = set()
    recursion_stack = set()
    for node_id in adjacency_list:
        if node_id not in visited:
            if _is_dag_cyclic_util(
                node_id, adjacency_list, visited, recursion_stack
            ):
                logger.error(f"在DAG中检测到循环，涉及节点: {node_id}")
                return True
    return False


# --- 依赖与节点辅助函数 (逻辑优化) ---

def _get_downstream_nodes(
    completed_node_id: str, edges: List[Dict]
) -> List[str]:
    """获取一个节点的所有直接下游节点。"""
    return [edge["to"] for edge in edges if edge["from"] == completed_node_id]


def _get_upstream_nodes(
    target_node_id: str, edges: List[Dict]
) -> List[str]:
    """获取一个节点的所有直接上游（依赖）节点。"""
    return [edge["from"] for edge in edges if edge["to"] == target_node_id]


def _are_dependencies_met(
    db: Session,
    target_node_id: str,
    workflow_instance_id: int,
    edges: List[Dict],
) -> bool:
    """检查一个节点的所有依赖任务是否都已成功完成。"""
    upstream_node_ids = _get_upstream_nodes(target_node_id, edges)
    if not upstream_node_ids:
        return True  # 没有依赖，条件满足

    completed_upstream_tasks_count = db.query(models.TaskInstance).filter(
        models.TaskInstance.workflow_instance_id == workflow_instance_id,
        models.TaskInstance.node_id.in_(upstream_node_ids),
        models.TaskInstance.status == "COMPLETED",
    ).count()

    return completed_upstream_tasks_count == len(upstream_node_ids)


# --- 新核心：基于任务组的分发逻辑 ---

def dispatch_task_group(
    db: Session, workflow_instance: models.WorkflowInstance, nodes_to_dispatch: List[Dict]
):
    """
    将一组可执行的节点打包成一个任务组，创建它们的数据库实例，
    并作为一个统一的载荷分发给异步Worker。
    """
    if not nodes_to_dispatch:
        return

    group_id = generate_nanoid(size=12)
    worker_payload_tasks = []
    task_instance_ids = []

    logger.info(f"为工作流 {workflow_instance.id} 创建任务组 '{group_id}'，包含 {len(nodes_to_dispatch)} 个节点。")

    for node_def in nodes_to_dispatch:
        node_id = node_def.get("id")
        agent_id = node_def.get("data", {}).get("agent_id")
        
        if not agent_id:
            logger.error(f"节点 '{node_id}' 未定义 'agent_id'，工作流失败。")
            workflow_instance.status = "FAILED"
            db.commit()
            return

        agent = crud.agent.get(db, id=agent_id)
        if not agent:
            logger.error(f"节点 '{node_id}' 的Agent ID '{agent_id}' 未找到，工作流失败。")
            workflow_instance.status = "FAILED"
            db.commit()
            return

        # 在数据库中创建任务实例
        task_instance_in = schemas.TaskInstanceCreate(
            node_id=node_id,
            status="PENDING",
            workflow_instance_id=workflow_instance.id,
            agent_id=agent_id,
            input_params=node_def.get("data", {}).get("input_params", {}),
        )
        task_instance = crud.task_instance.create(db, obj_in=task_instance_in)
        task_instance_ids.append(task_instance.id)

        # 为Worker准备任务载荷
        worker_payload_tasks.append({
            "task_instance_id": task_instance.id,
            "type": agent.agent_type.value,
            "source_reference": agent.source_reference, # 临时修复：直接传递路径
            "params": {
                "input_params": task_instance.input_params,
            }
        })

    # 准备发送给Worker的最终载荷
    payload = {
        "group_id": group_id,
        "tasks": worker_payload_tasks,
    }

    # 将整个任务组分发到新的Worker入口点
    celery_app.send_task("netbase.worker.execute_group", args=[payload], queue="compute_queue")
    logger.info(f"任务组 '{group_id}' (任务实例: {task_instance_ids}) 已分发至 compute_queue。")


# --- 重构后的核心事件处理器 ---

@celery_app.task(name="handle_scheduler_event", max_retries=3, default_retry_delay=5)
def handle_scheduler_event(event: dict):
    """
    处理调度事件的核心Celery任务。
    事件类型: START_WORKFLOW, TASK_COMPLETED, TASK_FAILED
    """
    db: Session = SessionLocal()
    try:
        event_type = event.get("event_type")
        logger.info(f"接收到调度事件: {event_type}, 数据: {event}")

        if event_type == "START_WORKFLOW":
            instance_id = event.get("instance_id")
            instance = crud.workflow_instance.get(db, id=instance_id)
            if not instance:
                logger.error(f"未找到工作流实例: {instance_id}")
                return

            dag_def = instance.dag_definition
            nodes = dag_def.get("nodes", [])
            edges = dag_def.get("edges", [])

            if is_dag_cyclic(nodes, edges):
                instance.status = "FAILED"
                db.commit()
                return

            # 找到所有入度为0的起始节点
            in_degree = {node["id"]: 0 for node in nodes}
            for edge in edges:
                if edge["to"] in in_degree:
                    in_degree[edge["to"]] += 1
            
            start_nodes_defs = [node for node in nodes if in_degree.get(node["id"]) == 0]

            if not start_nodes_defs:
                logger.error(f"工作流实例 {instance.id} 没有任何起始节点。")
                instance.status = "FAILED"
                db.commit()
                return

            instance.status = "RUNNING"
            db.commit()
            
            # 将所有起始节点作为一个任务组进行分发
            dispatch_task_group(db, instance, start_nodes_defs)

        elif event_type == "TASK_COMPLETED":
            task_instance_id = event.get("task_instance_id")
            task = crud.task_instance.get(db, id=task_instance_id)
            if not task:
                logger.error(f"未找到任务实例: {task_instance_id}")
                return

            workflow_instance = task.workflow_instance
            dag_def = workflow_instance.dag_definition
            nodes = dag_def.get("nodes", [])
            edges = dag_def.get("edges", [])

            # 寻找所有下游节点，检查它们的依赖是否已全部满足
            downstream_node_ids = _get_downstream_nodes(task.node_id, edges)
            newly_ready_nodes_defs = []
            for node_id in downstream_node_ids:
                # 检查此节点是否已被分发，防止竞争条件
                existing_task = db.query(models.TaskInstance).filter_by(
                    workflow_instance_id=workflow_instance.id, node_id=node_id
                ).first()
                if not existing_task and _are_dependencies_met(db, node_id, workflow_instance.id, edges):
                    node_def = next((n for n in nodes if n["id"] == node_id), None)
                    if node_def:
                        newly_ready_nodes_defs.append(node_def)

            # 将所有新就绪的节点作为一个任务组进行分发
            if newly_ready_nodes_defs:
                dispatch_task_group(db, workflow_instance, newly_ready_nodes_defs)

            # 检查整个工作流是否已完成
            all_tasks_count = len(nodes)
            completed_tasks_count = db.query(models.TaskInstance).filter(
                models.TaskInstance.workflow_instance_id == workflow_instance.id,
                models.TaskInstance.status == "COMPLETED"
            ).count()

            if all_tasks_count == completed_tasks_count:
                workflow_instance.status = "COMPLETED"
                db.commit()
                logger.info(f"工作流实例 {workflow_instance.id} 已成功完成。")

        elif event_type == "TASK_FAILED":
            task_instance_id = event.get("task_instance_id")
            task = crud.task_instance.get(db, id=task_instance_id)
            if task and task.workflow_instance.status != "FAILED":
                task.workflow_instance.status = "FAILED"
                db.commit()
                logger.error(f"任务 {task.id} 失败，工作流实例 {task.workflow_instance.id} 已被标记为失败。")

    except Exception as e:
        logger.critical(f"处理调度事件时发生严重错误: {e}", exc_info=True)
        # 可以选择让Celery根据配置进行重试
        # raise self.retry(exc=e)
    finally:
        db.close()