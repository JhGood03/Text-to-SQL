import json

from app.agtent.context import DataAgentContext
from app.agtent.graph import graph
from app.agtent.state import DataAgentState
from app.clients.embedding_client_manager import EmbeddingClientManager
from app.core.log import logger
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta.meta_mysql_reponsitory import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class QueryService:
    """问数查询服务，负责驱动智能体工作流并以 SSE 形式流式返回执行进度与结果。"""

    def __init__(self,
                 embedding_client: EmbeddingClientManager,
                 column_qdrant_repository: ColumnQdrantRepository,
                 value_es_repository: ValueEsRepository,
                 metric_qdrant_repository: MetricQdrantRepository,
                 meta_mysql_repository: MetaMysqlRepository,
                 dw_mysql_repository: DwMysqlRepository):
        """初始化查询服务。

        Args:
            embedding_client: 文本嵌入客户端管理器。
            column_qdrant_repository: 字段向量存储库。
            value_es_repository: 字段取值全文检索存储库。
            metric_qdrant_repository: 指标向量存储库。
            meta_mysql_repository: 元数据库存储库。
            dw_mysql_repository: 数据仓库存储库。
        """
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository

    async def query(self, query: str):
        """执行问数查询，流式产出 SSE 数据帧。

        Args:
            query: 用户的自然语言查询语句。

        Yields:
            符合 SSE 协议的数据帧字符串。
        """
        context = DataAgentContext(
            embedding_client=self.embedding_client,
            column_qdrant_repository=self.column_qdrant_repository,
            value_es_repository=self.value_es_repository,
            metric_qdrant_repository=self.metric_qdrant_repository,
            meta_mysql_repository=self.meta_mysql_repository,
            dw_mysql_repository=self.dw_mysql_repository
        )
        state = DataAgentState(query=query)

        logger.info(f"收到查询请求：{query}")
        try:
            async for chunk in graph.astream(input=state, context=context, stream_mode="custom"):
                # default=str 兜底处理 Decimal/date 等不可直接序列化的类型
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:
            logger.error(f"查询失败：{str(e)}")
            error = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error, ensure_ascii=False, default=str)}\n\n"
