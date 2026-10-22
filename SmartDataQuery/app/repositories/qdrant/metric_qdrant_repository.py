from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from app.conf.app_config import app_config
from app.core.log import logger
from app.models import MetricInfo


class MetricQdrantRepository:
    """指标信息存储库，提供对指标信息数据的持久化操作。"""
    collection_name = "metric_info_collection"
    _UPSERT_BATCH_SIZE = 100

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        """
        确保 Qdrant 中目标 collection 存在且向量维度配置正确。

        若 collection 已存在，则校验其向量维度是否与配置一致，不一致时抛出异常；
        若 collection 不存在，则按配置维度自动创建。

        Returns:
            None

        Raises:
            RuntimeError: 当已存在的 collection 向量维度与配置不一致时抛出。
        """

        exists = await self.client.collection_exists(
            self.collection_name
        )

        if exists:
            # 校验已有 collection 的向量维度是否与当前配置匹配，防止维度不一致导致写入失败
            info = await self.client.get_collection(
                self.collection_name
            )

            current_size = (
                info.config.params.vectors.size
            )

            if current_size != app_config.qdrant.embedding_size:
                raise RuntimeError(
                    f"""
                    Qdrant vector size mismatch.

                    Collection:
                    {current_size}

                    Config:
                    {app_config.qdrant.embedding_size}

                    Please recreate collection.
                    """
                )
            logger.info(f"Collection '{self.collection_name}' 已存在，向量维度校验通过 (size={current_size})")
            return

        # collection 不存在，按配置的向量维度创建新 collection
        logger.info(f"Collection '{self.collection_name}' 不存在，开始创建 (size={app_config.qdrant.embedding_size})")
        await self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=app_config.qdrant.embedding_size,
                distance=Distance.COSINE
            )
        )

    async def upsert_points(self, ids: list, embeddings: list, payloads: list):
        """批量写入或更新向量点数据，内部自动分批提交。

        Args:
            ids: 点 ID 列表。
            embeddings: 向量数据列表。
            payloads: 负载数据列表。

        Raises:
            ValueError: 当 ids、embeddings、payloads 三个列表长度不一致时抛出。
        """
        if not ids or not embeddings or not payloads:
            return

        if not (len(ids) == len(embeddings) == len(payloads)):
            raise ValueError(
                f"ids, embeddings, payloads 长度不一致: "
                f"len(ids)={len(ids)}, len(embeddings)={len(embeddings)}, len(payloads)={len(payloads)}"
            )

        for i in range(0, len(ids), self._UPSERT_BATCH_SIZE):
            batch_ids = ids[i:i + self._UPSERT_BATCH_SIZE]
            batch_embeddings = embeddings[i:i + self._UPSERT_BATCH_SIZE]
            batch_payloads = payloads[i:i + self._UPSERT_BATCH_SIZE]
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(id=point_id, vector=embedding, payload=payload)
                        for point_id, embedding, payload in zip(batch_ids, batch_embeddings, batch_payloads)]
            )
            logger.debug(f"Collection '{self.collection_name}' 写入批次 {i // self._UPSERT_BATCH_SIZE + 1}，本批 {len(batch_ids)} 条")

    async def search(self, embedding) -> list[MetricInfo]:
        """根据向量检索最相似的列信息。

        Args:
            embedding: 查询向量。
            limit: 返回的最大结果数量，默认为 5。

        Returns:
            匹配的搜索结果列表。
            :param embedding:
        """
        results = await self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=10,
            score_threshold=0.6,
            with_payload=True,
            with_vectors=False
        )
        return [MetricInfo(**point.payload) for point in results.points]