from langgraph.runtime import Runtime

from app.agtent.context import DataAgentContext
from app.agtent.state import DataAgentState
from app.core.log import logger


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """在数据仓库中校验 SQL 是否可执行，校验结果写入 error 字段。

    Args:
        state: 智能体状态，需包含 sql。
        runtime: 运行时对象，提供上下文依赖与流式输出能力。

    Returns:
        校验通过返回 {"error": None}，否则返回 {"error": 错误信息}。
    """
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "验证 SQL", "status": "running"})
    dw_mysql_repository = runtime.context["dw_mysql_repository"]
    sql = state["sql"]

    try:
        await dw_mysql_repository.validate_sql(sql)
        writer({"type": "progress", "step": "验证 SQL", "status": "success"})
        logger.info(f"SQL 验证成功：{sql}")
        return {"error": None}
    except Exception as e:
        writer({"type": "progress", "step": "验证 SQL", "status": "error"})
        logger.error(f"SQL 验证失败：{sql}，错误信息：{str(e)}")
        return {"error": str(e)}
