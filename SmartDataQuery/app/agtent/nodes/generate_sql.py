import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agtent.context import DataAgentContext
from app.agtent.llm import llm
from app.agtent.state import DataAgentState
from app.core.log import logger
from app.utils.load_prompt import load_prompt


async def generate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """根据召回的元数据上下文与用户问题生成 SQL。

    Args:
        state: 智能体状态，需包含 query、table_infos、metric_infos、date_info、db_info。
        runtime: 运行时对象，提供流式输出能力。

    Returns:
        包含生成结果 sql 的字典。
    """
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "生成 SQL", "status": "running"})

    query = state["query"]
    table_infos = state.get("table_infos", []) or []
    metric_infos = state.get("metric_infos", []) or []
    date_info = state.get("date_info", {})
    db_info = state.get("db_info", {})

    try:
        prompt = PromptTemplate(
            template=load_prompt("generate_sql"),
            input_variables=["query", "table_infos", "metric_infos", "date_info", "db_info"]
        )
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke(
            {
                "query": query,
                "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
                "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
                "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False),
                "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False)
            }
        )
        # 提示词已要求不要输出 Markdown 代码块，这里再做一次兜底清洗
        sql = result.strip().strip("`").removeprefix("sql").strip()

        writer({"type": "progress", "step": "生成 SQL", "status": "success"})
        logger.info(f"生成的 SQL：{sql}")
        return {"sql": sql}
    except Exception as e:
        writer({"type": "progress", "step": "生成 SQL", "status": "error"})
        logger.error(f"生成 SQL 失败：{str(e)}")
        raise
