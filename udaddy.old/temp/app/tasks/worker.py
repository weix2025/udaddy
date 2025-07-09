import shutil
from pathlib import Path
from app.tasks.wasm_manager import WasmManager

# 在Worker进程启动时创建WasmManager单例
# 这允许跨任务复用编译好的模块缓存和Wasmtime引擎
wasm_manager = WasmManager()
# app/tasks/worker.py

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from celery.exceptions import SoftTimeLimitExceeded

from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app import crud, models
from app.core.config import settings
from app.managers.workflow_manager import submit_to_scheduler

# --- WASM运行时和异步库的准备 ---
# 在实际部署时，请确保这些库已安装: pip install wasmtime aiohttp aiofiles
# from wasmtime import Config, Engine, Store, Module, Linker, WasiConfig
# import aiohttp
# import aiofiles

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


# --- 异步Agent执行逻辑 ---
# 每个函数代表一种Agent类型的具体实现，它们是并发执行的核心。

async def run_wasm_calculation(group_id: str, task_instance_id: int, source_reference: str, params: dict) -> dict:
    """
    通过WasmManager安全地执行一个WASM模块。
    """
    log_prefix = f"[{group_id}/{task_instance_id}/WASM]"
    logger.info(f"{log_prefix} - 开始执行。模块路径: '{source_reference}', 参数: {params}")

    # 为此任务创建一个唯一的、临时的安全工作区
    workspace_dir = Path(settings.SHARED_FS_ROOT) / "wasm_workspaces" / group_id / str(task_instance_id)
    
    try:
        # 确保工作区存在
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # 调用WasmManager的生产级执行器
        result = await wasm_manager.execute(
            group_id=group_id,
            task_instance_id=task_instance_id,
            module_path=source_reference,
            input_data=params.get("input_params", {}),
            workspace_dir=workspace_dir,
        )
        logger.info(f"{log_prefix} - WasmManager执行完毕，状态: {result['status']}.")
        return result

    except FileNotFoundError:
        error_msg = f"WASM模块文件未找到: {source_reference}"
        logger.error(f"{log_prefix} - {error_msg}")
        return {"status": "FAILED", "error": error_msg}
    except Exception as e:
        error_msg = f"执行WASM时发生未预料的错误: {e}"
        logger.critical(f"{log_prefix} - {error_msg}", exc_info=True)
        return {"status": "FAILED", "error": error_msg}
    finally:
        # 无论成功与否，都彻底清理工作区
        if workspace_dir.exists():
            try:
                shutil.rmtree(workspace_dir)
                logger.info(f"{log_prefix} - 临时工作区 '{workspace_dir}' 已被清理。")
            except OSError as e:
                logger.error(f"{log_prefix} - 清理工作区 '{workspace_dir}' 失败: {e}")


async def run_docker_container(group_id: str, task_instance_id: int, params: dict) -> dict:
    """
    (占位符) 异步执行一个Docker容器。
    """
    logger.info(f"[{group_id}/{task_instance_id}/DOCKER] - 开始执行。参数: {params}")
    
    # --- Docker SDK (异步) 伪代码 ---
    # try:
    #     image = params['agent_config']['source_reference']
    #     command = params['input_params'].get('command')
    #     # client = aiodocker.Docker()
    #     # container = await client.containers.create_or_replace(config={'Image': image, 'Cmd': command}, name=f"netbase-task-{task_instance_id}")
    #     # await container.start()
    #     # await container.wait()
    #     # logs = await container.log(stdout=True, stderr=True)
    #     # await container.delete()
    #     # await client.close()
    #     # return {"status": "SUCCESS", "output": {"logs": logs}}
    # except Exception as e:
    #     # ... 错误处理 ...
    
    await asyncio.sleep(5) # 模拟容器运行耗时
    output = {"container_id": f"sim_{task_instance_id}", "logs": "Container ran successfully."}
    logger.info(f"[{group_id}/{task_instance_id}/DOCKER] - 执行成功。")
    return {"status": "SUCCESS", "output": output}


async def run_python_function(group_id: str, task_instance_id: int, params: dict) -> dict:
    """
    (占位符) 异步执行一个通用的Python函数Agent。
    可以用于调用外部API等I/O密集型任务。
    """
    logger.info(f"[{group_id}/{task_instance_id}/PYTHON] - 开始执行。参数: {params}")
    
    # --- aiohttp 伪代码 ---
    # try:
    #     url = params['input_params'].get('url')
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(url) as response:
    #             response.raise_for_status()
    #             data = await response.json()
    #             return {"status": "SUCCESS", "output": data}
    # except Exception as e:
    #     # ... 错误处理 ...

    await asyncio.sleep(1) # 模拟I/O等待
    message = params.get("input_params", {}).get("message", "default message")
    output = {"response": f"Processed: {message}"}
    logger.info(f"[{group_id}/{task_instance_id}/PYTHON] - 执行成功。")
    return {"status": "SUCCESS", "output": output}


# --- 异步任务组执行器 ---

async def run_async_task_group(group_id: str, tasks_to_run: List[Dict]):
    """
    使用 TaskGroup 并发执行任务组内的所有子任务。
    这是异步Worker的核心调度逻辑。
    """
    db: Session = SessionLocal()
    try:
        logger.info(f"--- [Group: {group_id}] 开始执行任务组，包含 {len(tasks_to_run)} 个任务 ---")
        
        # 1. 批量更新任务状态为 RUNNING
        task_instance_ids = [t["task_instance_id"] for t in tasks_to_run]
        crud.task_instance.bulk_update_status(db, task_instance_ids=task_instance_ids, status=models.TaskStatus.RUNNING)

        # 2. 创建并并发执行所有协程任务
        async with asyncio.TaskGroup() as tg:
            async_tasks = {}
            for task_def in tasks_to_run:
                task_id = task_def["task_instance_id"]
                task_type = task_def.get("type")
                params = task_def.get("params", {})
                
                coro = None
                if task_type == models.AgentType.WASM.value:
                    coro = run_wasm_calculation(group_id, task_id, task_def.get("source_reference"), params)
                elif task_type == models.AgentType.DOCKER.value:
                    coro = run_docker_container(group_id, task_id, params)
                elif task_type == models.AgentType.PYTHON_FUNCTION.value:
                    coro = run_python_function(group_id, task_id, params)
                else:
                    logger.warning(f"[{group_id}/{task_id}] - 未知的Agent类型: {task_type}。将任务标记为失败。")
                    coro = asyncio.sleep(0, result={"status": "FAILED", "error": f"Unsupported agent type: {task_type}"})

                async_tasks[task_id] = tg.create_task(coro)

        # 3. 收集结果并批量更新数据库
        for task_id, task in async_tasks.items():
            result = task.result()
            task_instance = crud.task_instance.get(db, id=task_id)
            if task_instance:
                task_instance.status = models.TaskStatus.COMPLETED if result["status"] == "SUCCESS" else models.TaskStatus.FAILED
                task_instance.outputs = result.get("output")
                task_instance.logs = result.get("error")
                task_instance.completed_at = datetime.utcnow()
                db.add(task_instance)
        db.commit()

        # 4. 为每个完成或失败的任务提交调度事件
        for task_id, task in async_tasks.items():
            result = task.result()
            event_type = "TASK_COMPLETED" if result["status"] == "SUCCESS" else "TASK_FAILED"
            submit_to_scheduler({"event_type": event_type, "task_instance_id": task_id})

        logger.info(f"--- [Group: {group_id}] 任务组执行完毕 ---")

    except Exception as e:
        logger.critical(f"--- [Group: {group_id}] 任务组执行期间发生严重错误: {e} ---", exc_info=True)
        # 发生未知严重错误，将组内所有未完成的任务标记为失败
        task_instance_ids = [t["task_instance_id"] for t in tasks_to_run]
        crud.task_instance.bulk_fail_tasks(db, task_instance_ids=task_instance_ids, error_message=str(e))
        for task_id in task_instance_ids:
             submit_to_scheduler({"event_type": "TASK_FAILED", "task_instance_id": task_id})
    finally:
        db.close()


# --- Celery 入口点 ---

@celery_app.task(
    name="netbase.worker.execute_group",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    soft_time_limit=3600,
    time_limit=3700
)
def execute_group(self, payload: dict):
    """
    这是调度器实际调用的Celery任务。
    它接收一个包含 group_id 和 tasks 列表的载荷，并启动asyncio事件循环。
    """
    try:
        group_id = payload.get("group_id", "unknown_group")
        tasks = payload.get("tasks", [])

        if not tasks:
            logger.warning(f"接收到空的任务组: {group_id}")
            return

        asyncio.run(run_async_task_group(group_id, tasks))

    except SoftTimeLimitExceeded:
        logger.error(f"任务组 {payload.get('group_id')} 因超时而失败。")
        # 超时也需要将任务标记为失败
        db: Session = SessionLocal()
        try:
            task_ids = [t.get("task_instance_id") for t in payload.get("tasks", []) if t.get("task_instance_id")]
            crud.task_instance.bulk_fail_tasks(db, task_instance_ids=task_ids, error_message="Task group timed out.")
            for task_id in task_ids:
                submit_to_scheduler({"event_type": "TASK_FAILED", "task_instance_id": task_id})
        finally:
            db.close()
    except Exception as e:
        logger.critical(f"执行任务组 {payload.get('group_id')} 时发生顶层异常: {e}", exc_info=True)
        # 确保重试机制能被触发
        raise self.retry(exc=e)