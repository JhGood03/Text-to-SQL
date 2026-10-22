from sqlalchemy import Column, String, Text, JSON, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON
from app.models.base import Base


class ColumnInfo(Base):
    """列信息实体类"""
    __tablename__ = 'column_info'

    id = Column(String(64), primary_key=True, comment='列编号')
    name = Column(String(128), comment='列名称')
    type = Column(String(64), comment='数据类型')
    role = Column(String(32), comment='列类型(primary_key,foreign_key,measure,dimension)')
    examples = Column(JSON, comment='数据示例')
    description = Column(Text, comment='列描述')
    alias = Column(JSON, comment='列别名')
    table_id = Column(String(64), ForeignKey('table_info.id'), comment='所属表编号')

    # 关系：多对一，多个列属于一个表
    table = relationship('TableInfo', back_populates='columns')

    # 关系：多对多，通过中间表关联指标
    metrics = relationship('MetricInfo', secondary='column_metric', back_populates='columns')

    def __repr__(self):
        return f"<ColumnInfo(id={self.id}, name={self.name}, table_id={self.table_id})>"