# app/tasks/celery_app.py

from celery import Celery
from app.core.config import settings

# 创建Celery实例
# 第一个参数是当前项目的名称
# broker 和 backend 都使用配置文件中的Redis URL
celery_app = Celery(
    "netbase_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    # 自动发现并加载这些模块中的任务
    include=["app.tasks.worker", "app.tasks.scheduler"]
)

# Celery配置
celery_app.conf.update(
    # 任务执行时，将其状态更新为'STARTED'
    task_track_started=True,
    # 在启动时如果连接不上broker，会自动重试
    broker_connection_retry_on_startup=True,
    
    # --- 任务路由 ---
    # 这是实现调度器和计算Worker隔离的关键。
    # 它告诉Celery，哪个任务应该被发送到哪个队列。
    task_routes = {
        'app.tasks.scheduler.handle_scheduler_event': {'queue': 'scheduler_queue'},
        'app.tasks.worker.run_agent_task': {'queue': 'compute_queue'},
    }
)
