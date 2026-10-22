from qdrant_client import AsyncQdrantClient
from app.conf.app_config import QdrantConfig
from app.conf.app_config import app_config

class QdrantClientManager:
    """Qdrant 向量数据库客户端管理器，封装连接创建、释放及上下文管理。"""

    def __init__(self, config: QdrantConfig):
        """
        初始化客户端管理器。

        Args:
            config: Qdrant 连接配置，包含 host、port 等信息。
        """
        self.client: AsyncQdrantClient | None = None
        self.config: QdrantConfig = config

    def init(self):
        """
        初始化 Qdrant 客户端连接。

        若已存在客户端连接，先将其关闭以防止连接泄漏，再创建新连接。
        """
        # 防止重复创建导致连接泄漏
        if self.client is not None:
            self.client.close()
        self.client = AsyncQdrantClient(host=self.config.host, port=self.config.port)

    async def close(self):
        """关闭 Qdrant 客户端连接，并将 client 置为 None。"""
        if self.client is not None:
            await self.client.close()
            self.client = None



qdrant_client_manager = QdrantClientManager(app_config.qdrant)