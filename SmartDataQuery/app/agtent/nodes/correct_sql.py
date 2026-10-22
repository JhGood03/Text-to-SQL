import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agtent.context import DataAgentContext
from app.agtent.llm import llm
from app.agtent.state import DataAgentState
from app.core.log import logger
from app.utils.load_prompt import load_prompt


async def correct_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """根据 SQL 校验错误信息，让大模型进行最小必要修复。

    Args:
        state: 智能体状态，需包含 sql、error 及生成 SQL 所需的上下文。
        runtime: 运行时对象，提供流式输出能力。

    Returns:
        包含校正后 sql 的字典。
    """
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "校正 SQL", "status": "running"})

    sql = state["sql"]
    error = state.get("error")
    query = state["query"]
    table_infos = state.get("table_infos", []) or []
    metric_infos = state.get("metric_infos", []) or []
    date_info = state.get("date_info", {})
    db_info = state.get("db_info", {})

    try:
        prompt = PromptTemplate(
            template=load_prompt("correct_sql"),
            input_variables=["query", "table_infos", "metric_infos", "date_info", "db_info", "sql", "error"]
        )
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke(
            {
                "query": query,
                "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
                "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
                "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False),
                "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False),
                "sql": sql,
                "error": error
            }
        )
        corrected_sql = result.strip().strip("`").removeprefix("sql").strip()

        writer({"type": "progress", "step": "校正 SQL", "status": "success"})
        logger.info(f"校正后的 SQL：{corrected_sql}")
        return {"sql": corrected_sql}
    except Exception as e:
        writer({"type": "progress", "step": "校正 SQL", "status": "error"})
        logger.error(f"校正 SQL 失败：{str(e)}")
        raise
