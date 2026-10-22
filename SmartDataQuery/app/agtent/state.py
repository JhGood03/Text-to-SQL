from typing import TypedDict

from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo


class ColumnInfoState(TypedDict):
    """字段信息状态，用于承载最终送给大模型的精简字段结构。

    Attributes:
        name: 字段名。
        type: 数据类型。
        role: 字段角色。
        examples: 示例取值。
        description: 字段描述。
        alias: 字段别名。
    """
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]


class TableInfoState(TypedDict):
    """表信息状态，用于承载最终送给大模型的精简表结构。

    Attributes:
        name: 表名。
        role: 表类型（fact/dim）。
        description: 表描述。
        columns: 该表包含的字段列表。
    """
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]


class MetricInfoState(TypedDict):
    """指标信息状态，用于承载最终送给大模型的精简指标结构。

    Attributes:
        name: 指标名称。
        description: 指标描述（业务口径）。
        relevant_columns: 关联字段列表。
        alias: 指标别名。
    """
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


class DateInfoState(TypedDict):
    """日期信息状态，为 SQL 生成提供当前时间上下文。

    Attributes:
        date: 当前日期，格式 yyyy-MM-dd。
        weekday: 星期。
        quarter: 季度。
    """
    date: str
    weekday: str
    quarter: str


class DBInfoState(TypedDict):
    """数据库环境信息状态，约束生成 SQL 的语法方言。

    Attributes:
        dialect: 数据库方言，如 mysql。
        version: 数据库版本号。
    """
    dialect: str
    version: str


class DataAgentState(TypedDict, total=False):
    """问数智能体的全局状态。

    Attributes:
        query: 用户输入的查询语句。
        keywords: 从查询语句中抽取的关键词。
        retrieved_columns: 召回的字段信息。
        retrieved_values: 召回的字段取值信息。
        retrieved_metrics: 召回的指标信息。
        table_infos: 合并并过滤后的表信息。
        metric_infos: 合并并过滤后的指标信息。
        date_info: 当前日期信息。
        db_info: 数据仓库环境信息。
        sql: 生成的 SQL。
        error: 校验 SQL 时的错误信息，None 表示校验通过。
    """
    query: str
    keywords: list[str]
    retrieved_columns: list[ColumnInfo]
    retrieved_values: list[ValueInfo]
    retrieved_metrics: list[MetricInfo]
    table_infos: list[TableInfoState]
    metric_infos: list[MetricInfoState]
    date_info: DateInfoState
    db_info: DBInfoState
    sql: str
    error: str | None
