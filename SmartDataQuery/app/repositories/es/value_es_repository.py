from dataclasses import asdict
from typing import Sequence

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from app.entities.value_info import ValueInfo


class ValueEsRepository:
    """
    Elasticsearch ValueInfo 仓储。

    负责:
    - 索引初始化
    - ValueInfo 批量写入
    """

    index_name = "value_info"

    INDEX_MAPPING = {
        "dynamic": False,
        "properties": {
            "id": {
                "type": "keyword"
            },
            "value": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_max_word"
            },
            "column_id": {
                "type": "keyword"
            }
        }
    }

    def __init__(self, client: AsyncElasticsearch):
        self.client = client


    async def ensure_index(self) -> None:
        """
        确保索引存在。
        """

        exists = await self.client.indices.exists(
            index=self.index_name
        )

        if exists:
            return

        await self.client.indices.create(
            index=self.index_name,
            mappings=self.INDEX_MAPPING
        )


    async def index_values(
        self,
        value_info_list: Sequence[ValueInfo],
        chunk_size: int = 1000
    ) -> None:
        """
        批量写入 ValueInfo。

        Args:
            value_info_list:
                ValueInfo 数据列表

            chunk_size:
                ES bulk 批次大小
        """

        if not value_info_list:
            return


        actions = (
            {
                "_index": self.index_name,
                "_source": asdict(value_info) # type: ignore[arg-type]
            }
            for value_info in value_info_list
        )


        success, failed = await async_bulk(
            self.client,
            actions,
            chunk_size=chunk_size,
            refresh=False,
            raise_on_error=False
        )


        if failed:
            raise RuntimeError(
                f"ES bulk 写入失败数量: {len(failed)}"
            )

    async def search(self,keyword:str,score_threshold:float=0.6,limit:int = 20):
        resp = await self.client.search(
            index=self.index_name,
            query={
                "match": {
                    "value":keyword
                }
            },
            size=limit,
            min_score=score_threshold
        )
        return [ValueInfo(**hit['_source']) for hit in resp["hits"]["hits"]]