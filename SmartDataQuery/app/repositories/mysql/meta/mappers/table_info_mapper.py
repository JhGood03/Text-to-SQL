from dataclasses import asdict

from app.entities.table_info import TableInfo
from app.models.table_info import TableInfo as TableInfoMySQL


class TableInfoMapper:
    """TableInfo 业务实体与 SQLAlchemy 模型之间的转换器。"""

    @staticmethod
    def to_entity(table_info_mysql: TableInfoMySQL) -> TableInfo:
        """将 ORM 模型转换为业务实体。

        Args:
            table_info_mysql: 表信息 ORM 模型。

        Returns:
            表信息业务实体。
        """
        return TableInfo(
            id=table_info_mysql.id,
            name=table_info_mysql.name,
            role=table_info_mysql.role,
            description=table_info_mysql.description
        )

    @staticmethod
    def to_model(table_info: TableInfo) -> TableInfoMySQL:
        """将业务实体转换为 ORM 模型。

        Args:
            table_info: 表信息业务实体。

        Returns:
            表信息 ORM 模型。
        """
        return TableInfoMySQL(**asdict(table_info))
