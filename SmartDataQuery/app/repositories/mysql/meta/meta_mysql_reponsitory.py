from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.column_info import ColumnInfo
from app.entities.dto import ColumnDTO, ColumnMetricDTO, MetricDTO, TableDTO
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.models.column_info import ColumnInfo as ColumnInfoMySQL
from app.models.column_metric import ColumnMetric as ColumnMetricMySQL
from app.models.metric_info import MetricInfo as MetricInfoMySQL
from app.models.table_info import TableInfo as TableInfoMySQL
from app.repositories.mysql.meta.mappers.column_info_mapper import ColumnInfoMapper
from app.repositories.mysql.meta.mappers.metric_info_mapper import MetricInfoMapper
from app.repositories.mysql.meta.mappers.table_info_mapper import TableInfoMapper


class MetaMysqlRepository:
    """元数据存储库，用于管理元数据表和指标表。"""

    def __init__(self, session: AsyncSession):
        """
        初始化元数据存储库。

        Args:
            session: 元数据库的异步会话。
        """
        self.session = session

    # ------------------------------------------------------------------
    # 写入操作（元知识构建阶段）
    # ------------------------------------------------------------------
    async def save_tables(self, tables: list[TableDTO]):
        """批量保存表信息，内部完成 DTO 到 ORM 模型的转换和持久化。

        Args:
            tables: 表信息 DTO 列表。
        """
        for t in tables:
            await self.session.merge(TableInfoMySQL(**t.__dict__))

    async def save_columns(self, columns: list[ColumnDTO]):
        """批量保存列信息，内部完成 DTO 到 ORM 模型的转换和持久化。

        Args:
            columns: 列信息 DTO 列表。
        """
        for c in columns:
            await self.session.merge(ColumnInfoMySQL(**c.__dict__))

    async def save_metrics(self, metric_info_list: list[MetricDTO]):
        """批量保存指标信息，内部完成 DTO 到 ORM 模型的转换和持久化。

        Args:
            metric_info_list: 指标信息 DTO 列表。
        """
        for metric in metric_info_list:
            await self.session.merge(MetricInfoMySQL(**metric.__dict__))

    async def save_column_metrics(self, relevant_column_list: list[ColumnMetricDTO]):
        """批量保存列-指标关联关系，内部完成 DTO 到 ORM 模型的转换和持久化。

        Args:
            relevant_column_list: 列-指标关联 DTO 列表。
        """
        for column_metric in relevant_column_list:
            await self.session.merge(ColumnMetricMySQL(**column_metric.__dict__))

    async def commit(self):
        """提交当前事务，失败时自动回滚。"""
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    # ------------------------------------------------------------------
    # 查询操作（问数智能体召回信息合并阶段）
    # ------------------------------------------------------------------
    async def get_column_info_by_id(self, column_id: str) -> ColumnInfo | None:
        """按列编号查询列信息。

        Args:
            column_id: 列编号。

        Returns:
            列信息业务实体，不存在时返回 None。
        """
        result: ColumnInfoMySQL | None = await self.session.get(ColumnInfoMySQL, column_id)
        if result is None:
            return None
        return ColumnInfoMapper.to_entity(result)

    async def get_table_info_by_id(self, table_id: str) -> TableInfo | None:
        """按表编号查询表信息。

        Args:
            table_id: 表编号。

        Returns:
            表信息业务实体，不存在时返回 None。
        """
        result: TableInfoMySQL | None = await self.session.get(TableInfoMySQL, table_id)
        if result is None:
            return None
        return TableInfoMapper.to_entity(result)

    async def get_table_infos_by_ids(self, table_ids: list[str]) -> list[TableInfo]:
        """按表编号批量查询表信息。

        Args:
            table_ids: 表编号列表。

        Returns:
            表信息业务实体列表。
        """
        if not table_ids:
            return []
        sql = text("select * from table_info where id in :table_ids").bindparams(
            bindparam("table_ids", expanding=True)
        )
        result = await self.session.execute(sql, {"table_ids": table_ids})
        return [
            TableInfo(
                id=row.id,
                name=row.name,
                role=row.role,
                description=row.description
            )
            for row in result
        ]

    async def get_key_columns_by_table_id(self, table_id: str) -> list[ColumnInfo]:
        """查询指定表的主键与外键字段。

        多表关联生成 SQL 时需要显式补齐 join 条件所依赖的主外键字段。

        Args:
            table_id: 表编号。

        Returns:
            主键与外键列信息列表。
        """
        sql = """
            select *
            from column_info
            where table_id = :table_id
              and role in ('primary_key', 'foreign_key')
        """
        result = await self.session.execute(text(sql), {"table_id": table_id})
        return [ColumnInfoMapper.to_entity(row) for row in result.mappings().fetchall()]

    async def get_metric_info_by_id(self, metric_id: str) -> MetricInfo | None:
        """按指标编号查询指标信息。

        Args:
            metric_id: 指标编号。

        Returns:
            指标信息业务实体，不存在时返回 None。
        """
        result: MetricInfoMySQL | None = await self.session.get(MetricInfoMySQL, metric_id)
        if result is None:
            return None
        return MetricInfoMapper.to_entity(result)
