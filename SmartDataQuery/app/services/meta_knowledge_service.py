import uuid
from dataclasses import asdict
from pathlib import Path

from omegaconf import OmegaConf

from app.clients.embedding_client_manager import EmbeddingClientManager
from app.conf.meta_config import MetaConfig
from app.entities.dto import TableDTO, ColumnDTO, MetricDTO, ColumnMetricDTO
from app.entities.value_info import ValueInfo
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta.meta_mysql_reponsitory import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.core.log import logger

class MetaKnowledgeService:
    """元知识构建服务，负责从配置文件中读取元数据定义，
    结合数据仓库的实际表结构信息，构建并持久化元知识数据。
    """

    def __init__(self,
                 meta_mysql_repository:MetaMysqlRepository,
                 dw_mysql_repository:DwMysqlRepository,
                 column_qdrant_repository:ColumnQdrantRepository,
                 embedding_client_manager:EmbeddingClientManager,
                 value_es_repository:ValueEsRepository,
                 metric_qdrant_repository:MetricQdrantRepository
                 ):
        """初始化元知识构建服务。

        Args:
            meta_mysql_repository: 元数据存储库，用于将构建的元知识写入元数据库。
            dw_mysql_repository: 数据仓库存储库，用于查询数据仓库中的表结构和字段值。
        """
        self.meta_mysql_repository:MetaMysqlRepository = meta_mysql_repository
        self.dw_mysql_repository:DwMysqlRepository = dw_mysql_repository
        self.column_qdrant_repository:ColumnQdrantRepository = column_qdrant_repository
        self.embedding_client_manager:EmbeddingClientManager = embedding_client_manager
        self.value_es_repository:ValueEsRepository = value_es_repository
        self.metric_qdrant_repository:MetricQdrantRepository = metric_qdrant_repository

    async def build(self, config_path: Path):
        """根据配置文件构建元知识，编排各子流程完成元数据的持久化与索引构建。

        构建流程：
            1. 加载并解析配置文件。
            2. 同步表信息和列信息到元数据库。
            3. 对列信息建立向量索引。
            4. 对列值构建全文索引。
            5. 同步指标信息到元数据库。
            6. 对指标信息建立向量索引。

        Args:
            config_path: 配置文件路径，支持 OmegaConf 格式（YAML）。
        """
        meta_config = self._load_config(config_path)

        if meta_config.tables:
            logger.info(f"检测到 {len(meta_config.tables)} 张表，开始同步表和列元数据")
            column_info_list = await self._sync_table_and_column_meta(meta_config)
            logger.info(f"表和列元数据同步完成，共 {len(column_info_list)} 个列")
            logger.info("开始构建列向量索引")
            await self._build_column_vector_index(column_info_list)
            logger.info("列向量索引构建完成")
            logger.info("开始构建全文索引")
            await self._build_fulltext_index(meta_config)
            logger.info("全文索引构建完成")
        else:
            logger.info("配置中未定义表信息，跳过表和列相关流程")

        if meta_config.metrics:
            logger.info(f"检测到 {len(meta_config.metrics)} 个指标，开始同步指标元数据")
            metric_info_list = await self._sync_metric_meta(meta_config)
            logger.info(f"指标元数据同步完成，共 {len(metric_info_list)} 个指标")

            logger.info("开始构建指标向量索引")
            await self._build_metric_vector_index(metric_info_list)
            logger.info("指标向量索引构建完成")
        else:
            logger.info("配置中未定义指标信息，跳过指标相关流程")

        logger.info("元知识构建全部完成")

    @staticmethod
    def _load_config(config_path: Path) -> MetaConfig:
        """加载并解析配置文件，合并默认 schema 得到完整的元配置对象。

        Args:
            config_path: 配置文件路径，支持 OmegaConf 格式（YAML）。

        Returns:
            合并后的 MetaConfig 配置对象。
        """
        context = OmegaConf.load(config_path)
        schema = OmegaConf.structured(MetaConfig)
        return OmegaConf.to_object(OmegaConf.merge(schema, context))

    async def _sync_table_and_column_meta(self, meta_config: MetaConfig) -> list[ColumnDTO]:
        """将配置中的表信息和列信息同步到元数据库。

        遍历配置中定义的每张表，从数据仓库查询字段类型和示例值，
        构建 DTO 后批量写入元数据库并提交事务。

        Args:
            meta_config: 元配置对象，包含表和列的定义信息。

        Returns:
            构建好的列信息 DTO 列表，供后续向量索引使用。
        """
        table_info_list: list[TableDTO] = list()
        column_info_list: list[ColumnDTO] = list()
        # 遍历配置中定义的每张表，构建表信息和列信息
        for table in meta_config.tables:
            logger.debug(f"处理表: {table.name}")
            table_info = TableDTO(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description
            )
            table_info_list.append(table_info)

            # 查询出表的字段类型信息
            column_type: dict[str, str] = await self.dw_mysql_repository.get_column_type(table.name)

            for column in table.columns:
                # 查询字段中的实例数据
                column_value = await self.dw_mysql_repository.get_column_value_all(table.name, column.name)
                column_info = ColumnDTO(
                    id=column.name,
                    name=column.name,
                    type=column_type[column.name],
                    role=column.role,
                    examples=column_value,
                    description=column.description,
                    alias=column.alias,
                    table_id=table.name
                )
                column_info_list.append(column_info)
        # 批量持久化表信息和列信息到元数据库
        logger.debug(f"批量保存 {len(table_info_list)} 张表信息和 {len(column_info_list)} 个列信息到元数据库")
        await self.meta_mysql_repository.save_tables(table_info_list)
        await self.meta_mysql_repository.save_columns(column_info_list)
        await self.meta_mysql_repository.commit()
        return column_info_list

    async def _build_column_vector_index(self, column_info_list: list[ColumnDTO]):
        """对列信息建立向量索引，将列名、描述、别名的向量数据写入 Qdrant。

        Args:
            column_info_list: 列信息 DTO 列表。
        """
        # column_info的collection是否存在，如果不存在则创建
        await self.column_qdrant_repository.ensure_collection()

        # 构造需要保存的数据，直接构建三个平行列表
        ids: list = []
        texts: list = []
        payloads: list = []
        for column_info in column_info_list:
            # 列名
            ids.append(uuid.uuid4())
            texts.append(column_info.name)
            payloads.append(asdict(column_info)) # type: ignore[arg-type]

            # 列描述（过滤空值）
            if column_info.description:
                ids.append(uuid.uuid4())
                texts.append(column_info.description)
                payloads.append(asdict(column_info)) # type: ignore[arg-type]

            # 列别名（过滤空字符串）
            for alia in column_info.alias:
                if alia:
                    ids.append(uuid.uuid4())
                    texts.append(alia)
                    payloads.append(asdict(column_info)) # type: ignore[arg-type]
        logger.debug(f"列向量索引: 共 {len(ids)} 条向量数据待写入 Qdrant")
        # 批量生成向量嵌入
        embeddings = await self.embedding_client_manager.embed_documents(texts)
        logger.debug(f"列向量索引写入完成，共 {len(ids)} 条")
        # 将向量数据保存到Qdrant
        await self.column_qdrant_repository.upsert_points(ids, embeddings, payloads)

    async def _build_fulltext_index(self, meta_config: MetaConfig):
        """对配置中标记为需同步的列值构建 ES 全文索引。

        Args:
            meta_config: 元配置对象，包含表和列的定义信息。
        """
        # 判断是否已经创建全文索引，若没有，则创建
        await self.value_es_repository.ensure_index()
        # 构建全文索引
        value_info_list: list[ValueInfo] = []
        for table in meta_config.tables:
            for column in table.columns:
                if column.sync:
                    column_values = await self.dw_mysql_repository.get_column_value_all(table.name, column.name)
                    value_info = [ValueInfo(id=f"{table.name}.{column.name}.{column_value}",
                                            value=column_value,
                                            column_id=f"{table.name}.{column.name}")
                                  for column_value in column_values]
                    value_info_list.extend(value_info)

        await self.value_es_repository.index_values(value_info_list)

    async def _sync_metric_meta(self, meta_config: MetaConfig) -> list[MetricDTO]:
        """将配置中的指标信息及列-指标关联关系同步到元数据库。

        Args:
            meta_config: 元配置对象，包含指标的定义信息。

        Returns:
            构建好的指标信息 DTO 列表，供后续向量索引使用。
        """
        metric_info_list: list[MetricDTO] = list()
        relevant_column_list: list[ColumnMetricDTO] = list()
        for metric in meta_config.metrics:
            metric_info = MetricDTO(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias
            )
            metric_info_list.append(metric_info)
            for column in metric.relevant_columns:
                relevant_column = ColumnMetricDTO(
                    metric_id=metric.name,
                    column_id=column
                )
                relevant_column_list.append(relevant_column)
        logger.debug(f"批量保存 {len(metric_info_list)} 个指标和 {len(relevant_column_list)} 个列-指标关联到元数据库")
        await self.meta_mysql_repository.save_metrics(metric_info_list)
        await self.meta_mysql_repository.save_column_metrics(relevant_column_list)
        await self.meta_mysql_repository.commit()
        return metric_info_list

    async def _build_metric_vector_index(self, metric_info_list: list[MetricDTO]):
        """对指标信息建立向量索引。

        Args:
            metric_info_list: 指标信息 DTO 列表。
        """
        await self.metric_qdrant_repository.ensure_collection()

        # 构造需要保存的数据，直接构建三个平行列表
        ids: list = []
        texts: list = []
        payloads: list = []
        for metric_info in metric_info_list:
            # 列名
            ids.append(uuid.uuid4())
            texts.append(metric_info.name)
            payloads.append(asdict(metric_info)) # type: ignore[arg-type]

            # 列描述（过滤空值）
            if metric_info.description:
                ids.append(uuid.uuid4())
                texts.append(metric_info.description)
                payloads.append(asdict(metric_info)) # type: ignore[arg-type]

            # 列别名（过滤空字符串）
            for alia in metric_info.alias:
                if alia:
                    ids.append(uuid.uuid4())
                    texts.append(alia)
                    payloads.append(asdict(metric_info)) # type: ignore[arg-type]
        logger.debug(f"指标向量索引: 共 {len(ids)} 条向量数据待写入 Qdrant")
        # 批量生成向量嵌入
        embeddings = await self.embedding_client_manager.embed_documents(texts)

        # 将向量数据保存到Qdrant
        await self.metric_qdrant_repository.upsert_points(ids, embeddings, payloads)
        logger.debug(f"指标向量索引写入完成，共 {len(ids)} 条")