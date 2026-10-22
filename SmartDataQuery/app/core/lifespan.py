from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.core.log import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 生命周期管理，统一初始化与释放各外部存储客户端。

    Args:
        app: FastAPI 应用实例。
    """
    # 应用启动前执行
    logger.info("正在初始化外部存储客户端……")
    meta_mysql_client_manager.init()
    dw_mysql_client_manager.init()
    qdrant_client_manager.init()
    es_client_manager.init()
    await embedding_client_manager.init()
    logger.info("外部存储客户端初始化完成")

    yield

    # 应用结束前执行
    logger.info("正在释放外部存储客户端……")
    await qdrant_client_manager.close()
    await es_client_manager.close()
    await meta_mysql_client_manager.close()
    await dw_mysql_client_manager.close()
    logger.info("外部存储客户端已释放")
