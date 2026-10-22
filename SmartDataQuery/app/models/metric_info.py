from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON
from app.models.base import Base

class MetricInfo(Base):
    """指标信息实体类"""
    __tablename__ = 'metric_info'

    id = Column(String(64), primary_key=True, comment='指标编码')
    name = Column(String(128), comment='指标名称')
    description = Column(Text, comment='指标描述')
    relevant_columns = Column(JSON, comment='关联的列')
    alias = Column(JSON, comment='指标别名')

    # 关系：多对多，通过中间表关联列
    columns = relationship('ColumnInfo', secondary='column_metric', back_populates='metrics')

    def __repr__(self):
        return f"<MetricInfo(id={self.id}, name={self.name})>"