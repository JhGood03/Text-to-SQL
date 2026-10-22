from dataclasses import dataclass
from typing import Optional


@dataclass
class ColumnConfig:
    """
    列配置信息，用于描述数据库表中单个列的元数据。

    Attributes:
        name: 列名，对应数据库表中的字段名称。
        role: 列的角色，标识该列在业务逻辑中承担的功能角色。
        description: 列的描述信息，说明该列的业务含义。
        alias: 列的别名列表，用于支持多种名称映射。
        sync: 是否同步该列，控制该列是否参与数据同步流程。
    """
    name: str
    role: str
    description: str
    alias: list[str]
    sync: bool


@dataclass
class TableConfig:
    """
    表配置信息，用于描述数据库表的元数据及其包含的列配置。

    Attributes:
        name: 表名，对应数据库中的表名称。
        role: 表的角色，标识该表在业务逻辑中承担的功能角色。
        description: 表的描述信息，说明该表的业务用途。
        columns: 列配置列表，包含该表中所有列的配置信息。
    """
    name: str
    role: str
    description: str
    columns: list[ColumnConfig]


@dataclass
class MetricConfig:
    """
    指标配置信息，用于描述业务指标的定义及其关联的列。

    Attributes:
        name: 指标名称，标识该业务指标的唯一名称。
        description: 指标的描述信息，说明该指标的计算逻辑或业务含义。
        relevant_columns: 关联列名列表，指定该指标计算所依赖的列。
        alias: 指标的别名列表，用于支持多种名称映射。
    """
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


@dataclass
class MetaConfig:
    """
    元数据总配置，聚合表配置和指标配置，作为系统元数据的顶层容器。

    Attributes:
        tables: 表配置列表，可选，包含系统中所有表的配置信息。
        metrics: 指标配置列表，可选，包含系统中所有业务指标的配置信息。
    """
    tables: Optional[list[TableConfig]] = None
    metrics: Optional[list[MetricConfig]] = None
