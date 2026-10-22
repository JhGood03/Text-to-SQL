from dataclasses import dataclass, field
from typing import Any


@dataclass
class ColumnInfo:
    """列信息业务实体。

    Attributes:
        id: 列编号。
        name: 列名称。
        type: 数据类型。
        role: 列类型（primary_key/foreign_key/measure/dimension）。
        examples: 数据示例值列表。
        description: 列描述。
        alias: 列别名列表。
        table_id: 所属表编号。
    """
    id: str
    name: str
    type: str
    role: str
    examples: list[Any] = field(default_factory=list)
    description: str = ""
    alias: list[str] = field(default_factory=list)
    table_id: str = ""
