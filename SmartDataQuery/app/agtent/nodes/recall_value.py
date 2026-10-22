from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agtent.context import DataAgentContext
from app.agtent.llm import llm
from app.agtent.state import DataAgentState
from app.entities.value_info import ValueInfo
from app.utils.load_prompt import load_prompt
from app.core.log import logger


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """召回与用户问题相关的字段取值。

    先用大模型扩展取值候选关键词，再在 Elasticsearch 中做全文检索。

    Args:
        state: 智能体状态，需包含 query 与 keywords。
        runtime: 运行时对象，提供上下文依赖与流式输出能力。

    Returns:
        包含召回结果 retrieved_values 的字典。
    """
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回字段取值", "status": "running"})

    query = state["query"]
    keywords = state["keywords"]
    value_es_repository = runtime.context["value_es_repository"]

    try:
        # 扩展关键词
        prompt = PromptTemplate(
            template=load_prompt("extend_keywords_for_value_recall"),
            input_variables=["query"]
        )
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser
        result = await chain.ainvoke({"query": query})

        all_keywords = list(set(keywords + result))
        logger.info(f"召回字段取值扩展关键词：{all_keywords}")

        values_map: dict[str, ValueInfo] = {}
        for keyword in all_keywords:
            values: list[ValueInfo] = await value_es_repository.search(keyword)
            for value in values:
                if value.id not in values_map:
                    values_map[value.id] = value

        retrieved_values = list(values_map.values())

        writer({"type": "progress", "step": "召回字段取值", "status": "success"})
        logger.info(f"召回字段取值：{list(values_map.keys())}")
        return {"retrieved_values": retrieved_values}
    except Exception as e:
        writer({"type": "progress", "step": "召回字段取值", "status": "error"})
        logger.error(f"召回字段取值失败：{str(e)}")
        raise
