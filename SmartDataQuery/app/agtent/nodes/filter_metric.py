import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agtent.context import DataAgentContext
from app.agtent.llm import llm
from app.agtent.state import DataAgentState
from app.core.log import logger
from app.utils.load_prompt import load_prompt


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """借助大模型从候选指标中筛选出回答当前问题所必需的指标。

    Args:
        state: 智能体状态，需包含 query 与 metric_infos。
        runtime: 运行时对象，提供流式输出能力。

    Returns:
        包含过滤后 metric_infos 的字典。
    """
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤指标", "status": "running"})
    query = state["query"]
    metric_infos = list(state.get("metric_infos", []) or [])

    try:
        prompt = PromptTemplate(
            template=load_prompt("filter_metric_info"),
            input_variables=["query", "metric_infos"]
        )
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke(
            {
                "query": query,
                "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False)
            }
        )

        # 利用模型输出过滤 metric_infos，result 为指标名称列表，允许为空
        if not isinstance(result, list):
            raise ValueError(f"过滤指标的模型输出格式不正确：{result!r}")

        selected_metric_names = set(result)
        filtered_metric_infos = [
            metric_info
            for metric_info in metric_infos
            if metric_info["name"] in selected_metric_names
        ]

        writer({"type": "progress", "step": "过滤指标", "status": "success"})
        logger.info(f"过滤后的指标：{[metric_info['name'] for metric_info in filtered_metric_infos]}")
        return {"metric_infos": filtered_metric_infos}
    except Exception as e:
        writer({"type": "progress", "step": "过滤指标", "status": "error"})
        logger.error(f"过滤指标失败：{str(e)}")
        raise
