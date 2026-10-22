from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_query_service
from app.api.schemas.query_schema import QuerySchema
from app.services.query_service import QueryService

query_router = APIRouter()


@query_router.post("/api/query", summary="自然语言问数查询")
async def query(
    body: QuerySchema,
    query_service: QueryService = Depends(get_query_service)
):
    """接收自然语言查询，以 SSE 流式返回工作流执行进度与查询结果。

    Args:
        body: 请求体，包含用户查询语句。
        query_service: 由依赖注入提供的查询服务。

    Returns:
        SSE 流式响应。
    """
    return StreamingResponse(
        query_service.query(body.query),
        media_type="text/event-stream",
        headers={
            # 关闭反向代理缓冲，保证前端能实时收到进度
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
