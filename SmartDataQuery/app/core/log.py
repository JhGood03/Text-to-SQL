import sys
from pathlib import Path

from loguru import logger

from app.conf.app_config import app_config
from app.core.context import request_id_ctx_var

"""
全局日志配置模块。

根据 app_config 中的日志配置，初始化 loguru 日志系统，
同时支持控制台输出和文件输出，文件日志带有轮转与保留策略。
日志格式中额外输出 request_id，便于在并发场景下追踪单个请求的完整链路。
"""

# 日志输出格式模板：时间 | 日志级别 | request_id | 模块:函数:行号 - 消息
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<magenta>request_id - {extra[request_id]}</magenta> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def inject_request_id(record) -> None:
    """将当前上下文中的 request_id 注入到日志记录中。

    Args:
        record: loguru 的日志记录字典。
    """
    record["extra"]["request_id"] = request_id_ctx_var.get()


# 移除 loguru 默认的 stderr 处理器，避免重复输出
logger.remove()

# 给日志打补丁，使其支持注入 request_id
logger = logger.patch(inject_request_id)

# 根据配置决定是否启用控制台日志输出
if app_config.logging.console.enable:
    logger.add(sink=sys.stdout, level=app_config.logging.console.level, format=log_format)

# 根据配置决定是否启用文件日志输出，并应用轮转与保留策略
if app_config.logging.file.enable:
    path = Path(app_config.logging.file.path)
    path.mkdir(parents=True, exist_ok=True)
    logger.add(
        sink=path / "app.log",
        level=app_config.logging.file.level,
        format=log_format,
        rotation=app_config.logging.file.rotation,
        retention=app_config.logging.file.retention,
        encoding="utf-8",
    )
