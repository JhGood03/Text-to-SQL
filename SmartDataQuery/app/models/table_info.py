from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.models.base import Base


class TableInfo(Base):
    """表信息实体类"""
    __tablename__ = 'table_info'

    id = Column(String(64), primary_key=True, comment='表编号')
    name = Column(String(128), comment='表名称')
    role = Column(String(32), comment='表类型(fact/dim)')
    description = Column(Text, comment='表描述')

    # 关系：一对多，一个表有多个列
    columns = relationship('ColumnInfo', back_populates='table', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<TableInfo(id={self.id}, name={self.name}, role={self.role})>"