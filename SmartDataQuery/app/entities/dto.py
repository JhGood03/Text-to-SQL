from dataclasses import dataclass


@dataclass
class TableDTO:
    """表信息数据传输对象，与 ORM 框架无关的纯数据结构。"""
    id: str
    name: str
    role: str
    description: str


@dataclass
class ColumnDTO:
    """列信息数据传输对象，与 ORM 框架无关的纯数据结构。"""
    id: str
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list
    table_id: str


@dataclass
class MetricDTO:
    """指标信息数据传输对象，与 ORM 框架无关的纯数据结构。"""
    id: str
    name: str
    description: str
    relevant_columns: list
    alias: list


@dataclass
class ColumnMetricDTO:
    """列-指标关联关系数据传输对象，与 ORM 框架无关的纯数据结构。"""
    column_id: str
    metric_id: str
