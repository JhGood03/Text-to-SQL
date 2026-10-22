from sqlalchemy import Column, String,ForeignKey
from app.models.base import Base

class ColumnMetric(Base):
    """列-指标关联表实体类"""
    __tablename__ = 'column_metric'

    column_id = Column(String(64), ForeignKey('column_info.id'), primary_key=True, comment='列编号')
    metric_id = Column(String(64), ForeignKey('metric_info.id'), primary_key=True, comment='指标编号')

    def __repr__(self):
        return f"<ColumnMetric(column_id={self.column_id}, metric_id={self.metric_id})>"