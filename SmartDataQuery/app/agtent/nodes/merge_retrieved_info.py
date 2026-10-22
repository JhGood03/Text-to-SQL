from langgraph.runtime import Runtime

from app.agtent.context import DataAgentContext
from app.agtent.state import (
    ColumnInfoState,
    DataAgentState,
    MetricInfoState,
    TableInfoState,
)
from app.core.log import logger
from app.entities.column_info import ColumnInfo


async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """合并多路召回结果，组装出最终送给大模型的表信息与指标信息。

    处理流程：
        1. 将指标关联的字段补充进字段集合；
        2. 将召回到的字段取值补充进对应字段的示例中；
        3. 按所属表分组，并显式补齐每张表的主外键字段；
        4. 转换为精简的 TableInfoState / MetricInfoState 结构。

    Args:
        state: 智能体状态，需包含 retrieved_columns/retrieved_values/retrieved_metrics。
        runtime: 运行时对象，提供上下文依赖与流式输出能力。

    Returns:
        包含 table_infos 与 metric_infos 的字典。
    """
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "合并召回信息", "status": "running"})

    # 已召回的信息
    retrieved_columns = state.get("retrieved_columns", []) or []
    retrieved_values = state.get("retrieved_values", []) or []
    retrieved_metrics = state.get("retrieved_metrics", []) or []

    # 所需依赖
    meta_mysql_repository = runtime.context["meta_mysql_repository"]

    try:
        retrieved_columns_map: dict[str, ColumnInfo] = {
            retrieved_column.id: retrieved_column
            for retrieved_column in retrieved_columns
        }

        # 1. 将指标关联的字段补充进字段集合
        for retrieved_metric in retrieved_metrics:
            for relevant_column in retrieved_metric.relevant_columns:
                if relevant_column not in retrieved_columns_map:
                    column_info = await meta_mysql_repository.get_column_info_by_id(relevant_column)
                    if column_info is not None:
                        retrieved_columns_map[relevant_column] = column_info

        # 2. 将召回到的字段取值补充进字段的示例中
        for retrieved_value in retrieved_values:
            column_id = retrieved_value.column_id
            column_value = retrieved_value.value
            if column_id not in retrieved_columns_map:
                column_info = await meta_mysql_repository.get_column_info_by_id(column_id)
                if column_info is None:
                    continue
                retrieved_columns_map[column_id] = column_info
            examples = retrieved_columns_map[column_id].examples
            if column_value not in examples:
                examples.append(column_value)

        # 3. 按所属表分组
        table_to_columns_map: dict[str, list[ColumnInfo]] = {}
        for column in retrieved_columns_map.values():
            table_to_columns_map.setdefault(column.table_id, []).append(column)

        # 显式补充每张表的主外键，保证多表关联时 join 条件完整
        for table_id in table_to_columns_map.keys():
            key_columns: list[ColumnInfo] = await meta_mysql_repository.get_key_columns_by_table_id(table_id)
            column_ids = {column.id for column in table_to_columns_map[table_id]}
            for key_column in key_columns:
                if key_column.id not in column_ids:
                    table_to_columns_map[table_id].append(key_column)

        # 4. 转换为 TableInfoState 列表
        table_infos: list[TableInfoState] = []
        for table_id, columns in table_to_columns_map.items():
            table = await meta_mysql_repository.get_table_info_by_id(table_id)
            if table is None:
                logger.warning(f"元数据库中不存在表信息：{table_id}，已跳过")
                continue
            column_info_states: list[ColumnInfoState] = [
                ColumnInfoState(
                    name=column.name,
                    type=column.type,
                    role=column.role,
                    examples=column.examples,
                    description=column.description,
                    alias=column.alias
                )
                for column in columns
            ]
            table_infos.append(
                TableInfoState(
                    name=table.name,
                    role=table.role,
                    description=table.description,
                    columns=column_info_states
                )
            )

        # 处理指标信息
        metric_infos: list[MetricInfoState] = [
            MetricInfoState(
                name=metric_info.name,
                description=metric_info.description,
                relevant_columns=metric_info.relevant_columns,
                alias=metric_info.alias
            )
            for metric_info in retrieved_metrics
        ]

        writer({"type": "progress", "step": "合并召回信息", "status": "success"})
        logger.info(
            f"合并召回信息：表信息-{[table_info['name'] for table_info in table_infos]}，"
            f"指标信息-{[metric_info['name'] for metric_info in metric_infos]}"
        )
        return {"table_infos": table_infos, "metric_infos": metric_infos}
    except Exception as e:
        writer({"type": "progress", "step": "合并召回信息", "status": "error"})
        logger.error(f"合并召回信息失败：{str(e)}")
        raise
