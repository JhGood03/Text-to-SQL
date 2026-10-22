from dataclasses import dataclass


@dataclass
class TableInfo:
    """表信息业务实体。

    Attributes:
        id: 表编号，与数据仓库中的表名一致。
        name: 表名称。
        role: 表类型（fact/dim）。
        description: 表描述。
    """
    id: str
    name: str
    role: str
    description: str
