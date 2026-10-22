from datetime import datetime

from langgraph.runtime import Runtime

from app.agtent.context import DataAgentContext
from app.agtent.state import DataAgentState, DateInfoState, DBInfoState
from app.core.log import logger


async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """补充生成 SQL 所需的额外上下文：当前日期信息与数据仓库环境信息。

    Args:
        state: 智能体状态。
        runtime: 运行时对象，提供上下文依赖与流式输出能力。

    Returns:
        包含 date_info 与 db_info 的字典。
    """
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "添加额外上下文信息", "status": "running"})
    dw_mysql_repository = runtime.context["dw_mysql_repository"]

    try:
        # 当前的时间信息
        today = datetime.today()
        date = today.strftime("%Y-%m-%d")
        weekday = today.strftime("%A")
        quarter = f"Q{(today.month - 1) // 3 + 1}"
        date_info = DateInfoState(date=date, weekday=weekday, quarter=quarter)

        # 数据仓库环境信息
        db_info: DBInfoState = await dw_mysql_repository.get_db_info()

        writer({"type": "progress", "step": "添加额外上下文信息", "status": "success"})
        logger.info(f"额外上下文信息：数据库信息-{db_info}，日期信息-{date_info}")
        return {"date_info": date_info, "db_info": db_info}
    except Exception as e:
        writer({"type": "progress", "step": "添加额外上下文信息", "status": "error"})
        logger.error(f"添加上下文失败：{str(e)}")
        raise
