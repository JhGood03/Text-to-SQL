import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agtent.context import DataAgentContext
from app.agtent.llm import llm
from app.agtent.state import DataAgentState
from app.core.log import logger
from app.utils.load_prompt import load_prompt


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """借助大模型从候选表与字段中裁剪出回答当前问题所必需的部分。

    Args:
        state: 智能体状态，需包含 query 与 table_infos。
        runtime: 运行时对象，提供流式输出能力。

    Returns:
        包含过滤后 table_infos 的字典。
    """
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤表格", "status": "running"})
    query = state["query"]
    # 复制一份，避免就地修改上游状态中的列表对象
    table_infos = [dict(table_info) for table_info in state["table_infos"]]

    try:
        prompt = PromptTemplate(
            template=load_prompt("filter_table_info"),
            input_variables=["query", "table_infos"]
        )
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke(
            {
                "query": query,
                "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False)
            }
        )

        # 利用模型输出过滤 table_infos，result 形如：
        # {"fact_order": ["order_amount", "region_id"], "dim_region": ["region_id", "region_name"]}
        if not isinstance(result, dict):
            raise ValueError(f"过滤表格的模型输出格式不正确：{result!r}")

        filtered_table_infos = []
        for table_info in table_infos:
            if table_info["name"] not in result:
                continue
            selected_columns = set(result[table_info["name"]] or [])
            columns = [
                column_info
                for column_info in table_info["columns"]
                if column_info["name"] in selected_columns
            ]
            # 每张被选中的表必须至少保留一个字段，否则该表不应被保留
            if not columns:
                continue
            filtered_table_infos.append({**table_info, "columns": columns})

        writer({"type": "progress", "step": "过滤表格", "status": "success"})
        logger.info(f"过滤后的表信息：{[table_info['name'] for table_info in filtered_table_infos]}")
        return {"table_infos": filtered_table_infos}
    except Exception as e:
        writer({"type": "progress", "step": "过滤表格", "status": "error"})
        logger.error(f"过滤表格失败：{str(e)}")
        raise
