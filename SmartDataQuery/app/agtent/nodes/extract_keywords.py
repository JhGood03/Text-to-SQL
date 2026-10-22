import jieba.analyse
from langgraph.runtime import Runtime

from app.agtent.context import DataAgentContext
from app.agtent.state import DataAgentState
from app.core.log import logger

# 定义为模块级常量，避免每次函数调用时重复创建对象
ALLOW_POS = (
    "n",   # 名词
    "nr",  # 人名
    "ns",  # 地名
    "nt",  # 机构团体名
    "nz",  # 其他专名
    "v",   # 动词
    "vn",  # 名动词
    "a",   # 形容词
    "an",  # 名形词
    "eng", # 英文单词
    "i",   # 成语
    "l"    # 常用固定语
)


async def extract_keywords(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """从查询语句中抽取关键词。

    Args:
        state: 智能体状态，需包含 query。
        runtime: 运行时对象，提供流式输出能力。

    Returns:
        包含抽取结果 keywords 的字典。
    """
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "抽取关键字", "status": "running"})

    query = state.get("query", "")
    if not query:
        writer({"type": "progress", "step": "抽取关键字", "status": "success"})
        return {"keywords": []}

    # 使用 jieba 进行关键词提取，只保留具有业务含义的词性
    keywords = jieba.analyse.extract_tags(query, allowPOS=ALLOW_POS)

    # 与完整原句一起作为兜底，避免分词丢失语义
    keywords = list(set(keywords + [query]))

    writer({"type": "progress", "step": "抽取关键字", "status": "success"})
    logger.info(f"抽取关键词：{keywords}")
    return {"keywords": keywords}
