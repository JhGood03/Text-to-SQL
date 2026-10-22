from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agtent.context import DataAgentContext
from app.agtent.llm import llm
from app.agtent.state import DataAgentState
from app.entities.metric_info import MetricInfo
from app.utils.load_prompt import load_prompt
from app.core.log import logger


async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """召回与用户问题相关的指标信息。

    先用大模型扩展指标关键词，再将关键词向量化后在 Qdrant 中检索指标。

    Args:
        state: 智能体状态，需包含 query 与 keywords。
        runtime: 运行时对象，提供上下文依赖与流式输出能力。

    Returns:
        包含召回结果 retrieved_metrics 的字典。
    """
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回指标", "status": "running"})

    query = state["query"]
    keywords = state["keywords"]
    embedding_client = runtime.context["embedding_client"]
    metric_qdrant_repository = runtime.context["metric_qdrant_repository"]

    try:
        # 借助 LLM 扩展关键词
        prompt = PromptTemplate(
            template=load_prompt("extend_keywords_for_metric_recall"),
            input_variables=["query"]
        )
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser
        result = await chain.ainvoke({"query": query})

        all_keywords = list(set(keywords + result))
        logger.info(f"召回指标信息扩展关键词：{all_keywords}")

        retrieved_metrics_map: dict[str, MetricInfo] = {}
        for keyword in all_keywords:
            embedding = await embedding_client.embed_query(keyword)
            payloads: list[MetricInfo] = await metric_qdrant_repository.search(embedding)
            for payload in payloads:
                if payload.id not in retrieved_metrics_map:
                    retrieved_metrics_map[payload.id] = payload

        retrieved_metrics = list(retrieved_metrics_map.values())

        writer({"type": "progress", "step": "召回指标", "status": "success"})
        logger.info(f"召回指标信息：{list(retrieved_metrics_map.keys())}")
        return {"retrieved_metrics": retrieved_metrics}
    except Exception as e:
        writer({"type": "progress", "step": "召回指标", "status": "error"})
        logger.error(f"召回指标信息失败：{str(e)}")
        raise
