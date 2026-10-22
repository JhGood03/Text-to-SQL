from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agtent.context import DataAgentContext
from app.agtent.llm import llm
from app.agtent.state import DataAgentState
from app.entities.column_info import ColumnInfo
from app.utils.load_prompt import load_prompt
from app.core.log import logger


async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """召回与用户问题相关的字段信息。

    先用大模型扩展关键词，再将关键词向量化后在 Qdrant 中检索字段。

    Args:
        state: 智能体状态，需包含 query 与 keywords。
        runtime: 运行时对象，提供上下文依赖与流式输出能力。

    Returns:
        包含召回结果 retrieved_columns 的字典。
    """
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回字段", "status": "running"})

    query = state["query"]
    keywords = state["keywords"]
    embedding_client = runtime.context["embedding_client"]
    column_qdrant_repository = runtime.context["column_qdrant_repository"]

    try:
        # 1. 借助 LLM 扩展关键词
        prompt = PromptTemplate(
            template=load_prompt("extend_keywords_for_column_recall"),
            input_variables=["query"]
        )
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser
        result = await chain.ainvoke({"query": query})

        # 2. 使用扩展后的关键词召回字段信息
        all_keywords = list(set(keywords + result))
        logger.info(f"召回字段信息扩展关键词：{all_keywords}")

        retrieved_columns_map: dict[str, ColumnInfo] = {}
        for keyword in all_keywords:
            embedding = await embedding_client.embed_query(keyword)
            payloads: list[ColumnInfo] = await column_qdrant_repository.search(embedding)
            for payload in payloads:
                if payload.id not in retrieved_columns_map:
                    retrieved_columns_map[payload.id] = payload

        retrieved_columns = list(retrieved_columns_map.values())

        writer({"type": "progress", "step": "召回字段", "status": "success"})
        logger.info(f"召回字段信息：{list(retrieved_columns_map.keys())}")
        return {"retrieved_columns": retrieved_columns}
    except Exception as e:
        writer({"type": "progress", "step": "召回字段", "status": "error"})
        logger.error(f"召回字段信息失败：{str(e)}")
        raise
