import asyncio

from openai import AsyncOpenAI

from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddingClientManager:
    """异步文本嵌入客户端管理器，封装 OpenAI 兼容的嵌入 API 调用。

    负责初始化异步 OpenAI 客户端，并提供单条和批量文本向量化接口。
    内部自动完成客户端懒初始化，调用方无需手动调用 init()。
    """

    def __init__(self, config: EmbeddingConfig):
        """初始化客户端管理器。

        Args:
            config: 嵌入服务配置，包含 base_url、api_key、model 等信息。
        """
        self.client: AsyncOpenAI | None = None
        self.config: EmbeddingConfig = config
        self._model: str = config.model

    async def init(self) -> AsyncOpenAI:
        """懒初始化异步 OpenAI 客户端，重复调用直接返回已有实例。

        Returns:
            已初始化的 AsyncOpenAI 客户端实例。
        """
        if self.client is not None:
            return self.client
        self.client = AsyncOpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=30.0,
            max_retries=2
        )
        return self.client

    async def embed_query(self, text: str) -> list[float]:
        """将单条文本向量化，返回对应的嵌入向量。

        Args:
            text: 需要向量化的输入文本。

        Returns:
            浮点数列表，表示该文本的嵌入向量。
        """
        client = await self.init()
        response = await client.embeddings.create(
            model=self._model,
            input=text
        )
        return response.data[0].embedding

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量将多条文本向量化，返回对应的嵌入向量列表。

        内部按 batch_size 分批提交，避免单次请求文本量过大导致超时。

        Args:
            texts: 需要向量化的文本列表。

        Returns:
            二维浮点数列表，每个元素是一条文本的嵌入向量。
        """
        client = await self.init()
        batch_size = self.config.batch_size
        embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await client.embeddings.create(
                model=self._model,
                input=batch
            )
            embeddings.extend(data.embedding for data in response.data)
        return embeddings


# 全局单例，供整个应用复用
embedding_client_manager = EmbeddingClientManager(app_config.embedding)
if __name__ == '__main__':
    # 简单测试：向量化单条文本并打印结果
    async def main():

        result = await embedding_client_manager.embed_query("hello world")
        print(result)

    asyncio.run(main())
