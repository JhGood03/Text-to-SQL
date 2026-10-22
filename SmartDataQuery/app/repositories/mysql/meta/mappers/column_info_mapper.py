from dataclasses import asdict

from app.entities.column_info import ColumnInfo
from app.models.column_info import ColumnInfo as ColumnInfoMySQL


class ColumnInfoMapper:
    """ColumnInfo 业务实体与 SQLAlchemy 模型之间的转换器。"""

    @staticmethod
    def to_entity(column_info_mysql: ColumnInfoMySQL) -> ColumnInfo:
        """将 ORM 模型转换为业务实体。

        Args:
            column_info_mysql: 列信息 ORM 模型。

        Returns:
            列信息业务实体。
        """
        return ColumnInfo(
            id=column_info_mysql.id,
            name=column_info_mysql.name,
            type=column_info_mysql.type,
            role=column_info_mysql.role,
            examples=column_info_mysql.examples or [],
            description=column_info_mysql.description,
            alias=column_info_mysql.alias or [],
            table_id=column_info_mysql.table_id
        )

    @staticmethod
    def to_model(column_info: ColumnInfo) -> ColumnInfoMySQL:
        """将业务实体转换为 ORM 模型。

        Args:
            column_info: 列信息业务实体。

        Returns:
            列信息 ORM 模型。
        """
        return ColumnInfoMySQL(**asdict(column_info))
