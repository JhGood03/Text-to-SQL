from pydantic import BaseModel, Field


class QuerySchema(BaseModel):
    """查询接口请求体。

    Attributes:
        query: 用户的自然语言查询语句。
    """
    query: str = Field(..., description="用户的自然语言查询语句", min_length=1)
