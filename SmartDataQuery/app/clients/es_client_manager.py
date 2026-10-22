import asyncio

from elasticsearch import AsyncElasticsearch

from app.conf.app_config import ESConfig, app_config


class ESClientManager:
    """Elasticsearch 异步客户端管理器，封装客户端创建、关闭及上下文管理。"""

    def __init__(self, config: ESConfig):
        """
        初始化 ES 客户端管理器。

        Args:
            config: ES 连接配置，包含 host、port、index_name 等信息。
        """
        self.client: AsyncElasticsearch | None = None
        self.config: ESConfig = config

    def init(self):
        """
        初始化 Elasticsearch 异步客户端连接。

        若已存在客户端连接，先异步关闭旧连接以防止连接泄漏，再创建新连接。
        """
        if self.client is not None:
            import asyncio
            asyncio.create_task(self.client.close())
        self.client = AsyncElasticsearch(hosts=[self._get_url()])

    async def close(self):
        """关闭 Elasticsearch 客户端连接，并释放资源。"""
        if self.client is not None:
            await self.client.close()
            self.client = None

    def __enter__(self):
        """
        进入上下文时自动初始化 ES 客户端连接。

        Returns:
            ESClientManager 实例自身。
        """
        self.init()
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文时异步关闭 ES 客户端连接。

        Args:
            exc_type: 异常类型，若无异常则为 None。
            exc_val: 异常实例，若无异常则为 None。
            exc_tb: 异常回溯信息，若无异常则为 None。
        """
        import asyncio
        asyncio.create_task(self.close())


    def _get_url(self):
        """
        构建 ES 服务连接 URL。

        Returns:
            ES 服务 HTTP 连接地址字符串。
        """
        return f"http://{self.config.host}:{self.config.port}"

es_client_manager = ESClientManager(app_config.es)

if __name__ == '__main__':
    es_client_manager.init()
    client = es_client_manager.client

    async def test():
        # await client.indices.create(index="books")

        # await client.index(
        #     index="books",
        #     body={
        #         "name": "Three Kings",
        #         "author": "WuChengEn",
        #         "price": 10.0,
        #     }
        # )

        res = await client.search(index="books")
        print(res)

        await es_client_manager.close()
    asyncio.run(test())