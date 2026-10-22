from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.embedding_client_manager import EmbeddingClientManager, embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta.meta_mysql_reponsitory import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.query_service import QueryService


async def get_meta_session():
    """提供元数据库会话，请求结束后自动关闭。

    Yields:
        元数据库的异步会话。
    """
    async with meta_mysql_client_manager.session_factory() as session:
        yield session


async def get_dw_session():
    """提供数据仓库会话，请求结束后自动关闭。

    Yields:
        数据仓库的异步会话。
    """
    async with dw_mysql_client_manager.session_factory() as session:
        yield session


async def get_embedding_client() -> EmbeddingClientManager:
    """提供嵌入客户端管理器。

    Returns:
        全局嵌入客户端管理器单例。
    """
    return embedding_client_manager


async def get_column_qdrant_repository() -> ColumnQdrantRepository:
    """提供字段向量存储库。

    Returns:
        字段向量存储库实例。
    """
    return ColumnQdrantRepository(qdrant_client_manager.client)


async def get_value_es_repository() -> ValueEsRepository:
    """提供字段取值全文检索存储库。

    Returns:
        字段取值存储库实例。
    """
    return ValueEsRepository(es_client_manager.client)


async def get_metric_qdrant_repository() -> MetricQdrantRepository:
    """提供指标向量存储库。

    Returns:
        指标向量存储库实例。
    """
    return MetricQdrantRepository(qdrant_client_manager.client)


async def get_meta_mysql_repository(
    session: AsyncSession = Depends(get_meta_session)
) -> MetaMysqlRepository:
    """提供元数据存储库。

    Args:
        session: 由依赖注入提供的元数据库会话。

    Returns:
        元数据存储库实例。
    """
    return MetaMysqlRepository(session)


async def get_dw_mysql_repository(
    session: AsyncSession = Depends(get_dw_session)
) -> DwMysqlRepository:
    """提供数据仓库存储库。

    Args:
        session: 由依赖注入提供的数据仓库会话。

    Returns:
        数据仓库存储库实例。
    """
    return DwMysqlRepository(session)


async def get_query_service(
    embedding_client: EmbeddingClientManager = Depends(get_embedding_client),
    column_qdrant_repository: ColumnQdrantRepository = Depends(get_column_qdrant_repository),
    value_es_repository: ValueEsRepository = Depends(get_value_es_repository),
    metric_qdrant_repository: MetricQdrantRepository = Depends(get_metric_qdrant_repository),
    meta_mysql_repository: MetaMysqlRepository = Depends(get_meta_mysql_repository),
    dw_mysql_repository: DwMysqlRepository = Depends(get_dw_mysql_repository),
) -> QueryService:
    """组装问数查询服务，注入其全部依赖。

    Returns:
        已装配好依赖的查询服务实例。
    """
    return QueryService(
        embedding_client=embedding_client,
        column_qdrant_repository=column_qdrant_repository,
        value_es_repository=value_es_repository,
        metric_qdrant_repository=metric_qdrant_repository,
        meta_mysql_repository=meta_mysql_repository,
        dw_mysql_repository=dw_mysql_repository
    )
