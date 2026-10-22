from dataclasses import dataclass, field


@dataclass
class MetricInfo:
    """指标信息业务实体。

    Attributes:
        id: 指标编码。
        name: 指标名称。
        description: 指标描述（业务口径）。
        relevant_columns: 关联的列，格式为 表名.列名。
        alias: 指标别名列表。
    """
    id: str
    name: str
    description: str = ""
    relevant_columns: list[str] = field(default_factory=list)
    alias: list[str] = field(default_factory=list)
