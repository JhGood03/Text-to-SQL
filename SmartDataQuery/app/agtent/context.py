from typing import TypedDict

from app.clients.embedding_client_manager import EmbeddingClientManager
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta.meta_mysql_reponsitory import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class DataAgentContext(TypedDict):
    """问数智能体的运行时上下文，承载各节点所需的仓储与客户端依赖。

    Attributes:
        embedding_client: 文本嵌入客户端管理器。
        column_qdrant_repository: 字段向量存储库。
        value_es_repository: 字段取值全文检索存储库。
        metric_qdrant_repository: 指标向量存储库。
        meta_mysql_repository: 元数据库存储库。
        dw_mysql_repository: 数据仓库存储库。
    """
    embedding_client: EmbeddingClientManager
    column_qdrant_repository: ColumnQdrantRepository
    value_es_repository: ValueEsRepository
    metric_qdrant_repository: MetricQdrantRepository
    meta_mysql_repository: MetaMysqlRepository
    dw_mysql_repository: DwMysqlRepository
