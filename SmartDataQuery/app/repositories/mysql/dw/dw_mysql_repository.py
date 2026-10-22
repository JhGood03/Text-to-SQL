from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DwMysqlRepository:
    """数据仓库存储库，用于管理数据仓库表和指标表。"""

    def __init__(self, session: AsyncSession):
        """
        初始化数据仓库存储库。

        Args:
            session: 数据仓库的异步会话。
        """
        self.session = session

    async def get_column_type(self, table_name):
        """查询表的所有字段及其数据类型。

        Args:
            table_name: 表名。

        Returns:
            字段名到数据类型的映射。
        """
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        result_dict = result.mappings().fetchall()
        return {row['Field']: row['Type'] for row in result_dict}

    async def get_column_value(self, table_name, column_name):
        """查询字段的去重取值（最多返回 5 个），用于采样示例值。

        Args:
            table_name: 表名。
            column_name: 字段名。

        Returns:
            去重后的字段取值列表。
        """
        sql = f"select distinct {column_name} from {table_name} limit 5"
        result = await self.session.execute(text(sql))
        return [row[0] for row in result.fetchall()]

    async def get_column_value_all(self, table_name, column_name):
        """查询字段的全部去重取值。

        Args:
            table_name: 表名。
            column_name: 字段名。

        Returns:
            全量去重后的字段取值列表。
        """
        sql = f"select distinct {column_name} from {table_name}"
        result = await self.session.execute(text(sql))
        return [row[0] for row in result.fetchall()]

    async def get_db_info(self) -> dict:
        """获取数据仓库的数据库环境信息。

        Returns:
            包含数据库版本与方言的字典，如 {"version": "...", "dialect": "mysql"}。
        """
        result = await self.session.execute(text("select version()"))
        version = result.scalar()
        dialect = self.session.get_bind().dialect.name
        return {"version": version, "dialect": dialect}

    async def validate_sql(self, sql: str):
        """校验 SQL 是否可在数据仓库中执行。

        通过 EXPLAIN 让数据库解析并生成执行计划，语法或语义有误时会抛出异常。

        Args:
            sql: 待校验的 SQL 语句。

        Raises:
            Exception: SQL 语法错误、表或字段不存在等。
        """
        await self.session.execute(text(f"explain {sql}"))

    async def execute_sql(self, sql: str) -> list[dict]:
        """执行查询 SQL 并返回结果集。

        Args:
            sql: 待执行的查询 SQL。

        Returns:
            结果集，每行是一个字典。
        """
        result = await self.session.execute(text(sql))
        return [dict(row) for row in result.mappings().fetchall()]
