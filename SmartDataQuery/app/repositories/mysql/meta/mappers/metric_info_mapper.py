from dataclasses import asdict

from app.entities.metric_info import MetricInfo
from app.models.metric_info import MetricInfo as MetricInfoMySQL


class MetricInfoMapper:
    """MetricInfo 业务实体与 SQLAlchemy 模型之间的转换器。"""

    @staticmethod
    def to_entity(metric_info_mysql: MetricInfoMySQL) -> MetricInfo:
        """将 ORM 模型转换为业务实体。

        Args:
            metric_info_mysql: 指标信息 ORM 模型。

        Returns:
            指标信息业务实体。
        """
        return MetricInfo(
            id=metric_info_mysql.id,
            name=metric_info_mysql.name,
            description=metric_info_mysql.description,
            relevant_columns=metric_info_mysql.relevant_columns or [],
            alias=metric_info_mysql.alias or []
        )

    @staticmethod
    def to_model(metric_info: MetricInfo) -> MetricInfoMySQL:
        """将业务实体转换为 ORM 模型。

        Args:
            metric_info: 指标信息业务实体。

        Returns:
            指标信息 ORM 模型。
        """
        return MetricInfoMySQL(**asdict(metric_info))
