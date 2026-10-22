from langgraph.runtime import Runtime

from app.agtent.context import DataAgentContext
from app.agtent.state import DataAgentState
from app.core.log import logger


async def execute_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """在数据仓库中执行 SQL，并将查询结果流式推送给前端。

    Args:
        state: 智能体状态，需包含 sql。
        runtime: 运行时对象，提供上下文依赖与流式输出能力。

    Returns:
        空字典，查询结果已通过 stream_writer 推送。
    """
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "执行 SQL", "status": "running"})
    sql = state["sql"]

    dw_mysql_repository = runtime.context["dw_mysql_repository"]
    try:
        result = await dw_mysql_repository.execute_sql(sql)

        writer({"type": "progress", "step": "执行 SQL", "status": "success"})
        writer({"type": "result", "data": result})
        logger.info(f"执行 SQL 结果：{result}")
        return {}
    except Exception as e:
        writer({"type": "progress", "step": "执行 SQL", "status": "error"})
        logger.error(f"执行 SQL 失败：{str(e)}")
        raise
