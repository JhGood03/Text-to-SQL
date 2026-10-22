from dataclasses import dataclass


@dataclass
class ColumnMetric:
    """列与指标关联关系业务实体。

    Attributes:
        column_id: 列编号。
        metric_id: 指标编号。
    """
    column_id: str
    metric_id: str
