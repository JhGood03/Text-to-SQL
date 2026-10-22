from dataclasses import asdict

from app.entities.column_metric import ColumnMetric
from app.models.column_metric import ColumnMetric as ColumnMetricMySQL


class ColumnMetricMapper:
    """ColumnMetric 业务实体与 SQLAlchemy 模型之间的转换器。"""

    @staticmethod
    def to_entity(column_metric_mysql: ColumnMetricMySQL) -> ColumnMetric:
        """将 ORM 模型转换为业务实体。

        Args:
            column_metric_mysql: 列-指标关联 ORM 模型。

        Returns:
            列-指标关联业务实体。
        """
        return ColumnMetric(
            column_id=column_metric_mysql.column_id,
            metric_id=column_metric_mysql.metric_id
        )

    @staticmethod
    def to_model(column_metric: ColumnMetric) -> ColumnMetricMySQL:
        """将业务实体转换为 ORM 模型。

        Args:
            column_metric: 列-指标关联业务实体。

        Returns:
            列-指标关联 ORM 模型。
        """
        return ColumnMetricMySQL(**asdict(column_metric))
