# app/tasks/wasm_manager.py (新文件)

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict

from wasmtime import (Config, Engine, Instance, Linker, Memory, Module, Store,
                      Trap, WasiConfig)

# 从app的核心配置中获取日志级别和其它设置
from app.core.config import settings

logger = logging.getLogger(__name__)

# 为WASM执行定义合理的资源限制
# 这个值需要根据实际任务进行调整和测试
DEFAULT_WASM_FUEL = 100_000_000  # 约等于几百毫秒的纯计算时间

class WasmManager:
    """
    一个封装了Wasmtime运行时复杂性的生产级管理器。
    负责模块缓存、实例创建、资源限制和安全执行。
    设计为在每个Worker进程中作为单例存在。
    """
    _engine: Engine
    _module_cache: Dict[str, Module]

    def __init__(self):
        logger.info("Initializing WasmManager for production...")
        config = Config()
        config.async_support = True
        config.consume_fuel = True  # 开启Fuel机制，防止无限循环
        self._engine = Engine(config)
        self._module_cache = {}
        logger.info("Wasmtime Engine created with async support and fuel consumption enabled.")

    async def _get_module(self, module_path: str) -> Module:
        """
        从缓存中异步获取已编译的模块，或在首次加载时进行编译。
        这避免了每次执行任务时重复编译WASM字节码的开销。
        """
        if module_path not in self._module_cache:
            logger.info(f"Compiling and caching WASM module for the first time: {module_path}")
            try:
                self._module_cache[module_path] = await Module.from_file_async(self._engine, module_path)
            except Exception as e:
                logger.error(f"Failed to compile WASM module {module_path}: {e}")
                raise
        return self._module_cache[module_path]

    async def execute(
        self,
        group_id: str,
        task_instance_id: int,
        module_path: str,
        input_data: Dict[str, Any],
        workspace_dir: Path
    ) -> Dict[str, Any]:
        """
        安全地执行WASM模块。
        此方法实现了资源限制、权限隔离和标准化的数据交换协议。
        """
        log_prefix = f"[{group_id}/{task_instance_id}/WASM]"
        
        # 确保安全的工作区目录存在
        workspace_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. 配置Store，为本次执行设置资源限制
            store = Store(self._engine)
            store.add_fuel(DEFAULT_WASM_FUEL)
            store.set_time_limit(5.0) # 设置5秒的墙钟超时

            # 2. 配置Linker和WASI，构建沙箱环境
            linker = Linker(self._engine)
            
            wasi_config = WasiConfig()
            wasi_config.inherit_stdout() # 允许WASM的日志输出到Worker的stdout
            wasi_config.inherit_stderr()
            # 将宿主的安全工作区目录映射为WASM内部的根目录'/'
            # 这是实现文件系统隔离的关键
            wasi_config.preopen_dir(str(workspace_dir), "/")
            store.set_wasi(wasi_config)
            linker.define_wasi()

            # 3. 获取模块并实例化
            module = await self._get_module(module_path)
            instance = await linker.instantiate_async(store, module)

            # 4. 实现自定义的内存投递协议
            memory = instance.exports(store).get("memory")
            if not isinstance(memory, Memory):
                raise TypeError("WASM module must export a 'memory' object.")

            allocate_func = instance.exports(store).get("allocate_memory")
            free_func = instance.exports(store).get("free_memory")
            run_func = instance.exports(store).get("run")

            if not all([allocate_func, free_func, run_func]):
                raise TypeError("WASM module must export 'allocate_memory', 'free_memory', and 'run' functions for custom data passing.")

            # 4a. 写入输入数据
            input_bytes = json.dumps(input_data).encode('utf-8')
            input_size = len(input_bytes)
            input_ptr = await allocate_func(store, input_size)
            if not isinstance(input_ptr, int): raise TypeError("allocate_memory must return an integer pointer.")
            
            memory.write(store, input_bytes, input_ptr)
            logger.debug(f"{log_prefix} - Wrote {input_size} input bytes to WASM memory at ptr {input_ptr}.")

            # 4b. 执行核心逻辑
            logger.info(f"{log_prefix} - Starting WASM execution...")
            packed_result = await run_func(store, input_ptr, input_size)
            if not isinstance(packed_result, int): raise TypeError("run function must return a packed integer (u64).")
            logger.info(f"{log_prefix} - WASM execution finished.")

            # 4c. 读回输出数据
            output_ptr = packed_result >> 32
            output_size = packed_result & 0xFFFFFFFF
            
            if output_size == 0:
                 # 正常情况，可能没有输出
                output_str = "{}"
            else:
                output_bytes = memory.read(store, output_ptr, output_ptr + output_size)
                output_str = output_bytes.decode('utf-8').rstrip('\x00')

            logger.debug(f"{log_prefix} - Read {output_size} output bytes from WASM memory at ptr {output_ptr}.")
            
            # 4d. 清理WASM内存
            await free_func(store, input_ptr, input_size)
            if output_size > 0:
                await free_func(store, output_ptr, output_size)
            
            # 5. 成功返回
            return {"status": "SUCCESS", "output": json.loads(output_str)}

        except Trap as trap:
            # 捕获特定的Wasmtime异常，如燃料耗尽、超时、内存越界等
            error_message = f"WASM execution trapped: {trap}"
            logger.error(f"{log_prefix} - {error_message}")
            return {"status": "FAILED", "error": error_message}
        except Exception as e:
            # 捕获其它所有异常，如文件未找到、函数未导出等
            logger.error(f"{log_prefix} - An unexpected error occurred: {e}", exc_info=True)
            return {"status": "FAILED", "error": str(e)}