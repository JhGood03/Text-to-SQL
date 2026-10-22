import asyncio

from langgraph.graph import StateGraph, START, END

from app.agtent.context import DataAgentContext
from app.agtent.nodes.add_extra_context import add_extra_context
from app.agtent.nodes.correct_sql import correct_sql
from app.agtent.nodes.execute_sql import execute_sql
from app.agtent.nodes.extract_keywords import extract_keywords
from app.agtent.nodes.filter_metric import filter_metric
from app.agtent.nodes.filter_table import filter_table
from app.agtent.nodes.generate_sql import generate_sql
from app.agtent.nodes.merge_retrieved_info import merge_retrieved_info
from app.agtent.nodes.recall_column import recall_column
from app.agtent.nodes.recall_value import recall_value
from app.agtent.nodes.recall_metric import recall_metric
from app.agtent.nodes.validate_sql import validate_sql
from app.agtent.state import DataAgentState
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta.meta_mysql_reponsitory import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository

builder = StateGraph(state_schema=DataAgentState, context_schema=DataAgentContext)

# 添加节点
builder.add_node("extract_keywords", extract_keywords)  # 抽取关键信息
builder.add_node("recall_column", recall_column)  # 召回字段信息
builder.add_node("recall_value", recall_value)  # 召回字段取值
builder.add_node("recall_metric", recall_metric)  # 召回指标信息
builder.add_node("merge_retrieved_info", merge_retrieved_info)  # 合并召回信息
builder.add_node("filter_metric", filter_metric)  # 过滤指标信息
builder.add_node("filter_table", filter_table)  # 过滤表信息
builder.add_node("add_extra_context", add_extra_context)  # 添加额外上下文
builder.add_node("generate_sql", generate_sql)  # 生成 SQL
builder.add_node("validate_sql", validate_sql)  # 校验 SQL
builder.add_node("correct_sql", correct_sql)  # 校正 SQL
builder.add_node("execute_sql", execute_sql)  # 执行 SQL

# 添加关系
builder.add_edge(START, "extract_keywords")
builder.add_edge("extract_keywords", "recall_column")
builder.add_edge("extract_keywords", "recall_value")
builder.add_edge("extract_keywords", "recall_metric")
builder.add_edge("recall_column", "merge_retrieved_info")
builder.add_edge("recall_value", "merge_retrieved_info")
builder.add_edge("recall_metric", "merge_retrieved_info")
builder.add_edge("merge_retrieved_info", "filter_table")
builder.add_edge("merge_retrieved_info", "filter_metric")
builder.add_edge("filter_table", "add_extra_context")
builder.add_edge("filter_metric", "add_extra_context")
builder.add_edge("add_extra_context", "generate_sql")
builder.add_edge("generate_sql", "validate_sql")


def validate_fun(state: DataAgentState):
    """根据 SQL 校验结果决定下一步走向。

    Args:
        state: 智能体状态，error 为 None 表示校验通过。

    Returns:
        "execute_sql" 或 "correct_sql"。
    """
    if state["error"] is None:
        return "execute_sql"
    return "correct_sql"


builder.add_conditional_edges(
    source="validate_sql",
    path=validate_fun,
    path_map={"execute_sql": "execute_sql", "correct_sql": "correct_sql"}
)
builder.add_edge("correct_sql", "execute_sql")
builder.add_edge("execute_sql", END)

graph = builder.compile()


if __name__ == '__main__':
    async def run():
        """本地调试入口：初始化各存储客户端并跑通整条问数链路。"""
        meta_mysql_client_manager.init()
        dw_mysql_client_manager.init()
        qdrant_client_manager.init()
        await embedding_client_manager.init()
        es_client_manager.init()

        async with (
            meta_mysql_client_manager.session_factory() as meta_session,
            dw_mysql_client_manager.session_factory() as dw_session
        ):
            context = DataAgentContext(
                embedding_client=embedding_client_manager,
                column_qdrant_repository=ColumnQdrantRepository(qdrant_client_manager.client),
                value_es_repository=ValueEsRepository(es_client_manager.client),
                metric_qdrant_repository=MetricQdrantRepository(qdrant_client_manager.client),
                meta_mysql_repository=MetaMysqlRepository(meta_session),
                dw_mysql_repository=DwMysqlRepository(dw_session)
            )
            state = DataAgentState(query="统计去年各地区的销售总额")
            async for chunk in graph.astream(input=state, context=context, stream_mode="custom"):
                print(chunk)

        await qdrant_client_manager.close()
        await es_client_manager.close()
        await meta_mysql_client_manager.close()
        await dw_mysql_client_manager.close()

    asyncio.run(run())
