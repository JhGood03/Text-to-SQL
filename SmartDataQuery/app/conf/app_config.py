# 日志配置
import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from omegaconf import OmegaConf

"""
文件日志输出配置。

Attributes:
    enable: 是否启用文件日志。
    level: 日志级别，如 DEBUG、INFO、WARNING、ERROR。
    path: 日志文件的存储路径。
    rotation: 日志轮转策略，如按大小或时间轮转。
    retention: 日志保留时长或备份数量。
"""
@dataclass
class File:
    enable: bool
    level: str
    path: str
    rotation: str
    retention: str

"""
控制台日志输出配置。

Attributes:
    enable: 是否启用控制台日志。
    level: 日志级别，如 DEBUG、INFO、WARNING、ERROR。
"""
@dataclass
class Console:
    enable: bool
    level: str

"""
日志配置聚合，组合文件日志和控制台日志配置。

Attributes:
    file: 文件日志输出配置。
    console: 控制台日志输出配置。
"""
@dataclass
class LoggingConfig:
    file: File
    console: Console

# 数据库配置
"""
关系型数据库连接配置。

Attributes:
    host: 数据库主机地址。
    port: 数据库服务端口号。
    user: 数据库登录用户名。
    password: 数据库登录密码。
    database: 目标数据库名称。
"""
@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

"""
Qdrant 向量数据库连接配置。

Attributes:
    host: Qdrant 服务主机地址。
    port: Qdrant 服务端口号。
    embedding_size: 向量嵌入维度大小。
"""
@dataclass
class QdrantConfig:
    host: str
    port: int
    embedding_size: int

"""
文本嵌入模型服务连接配置。

Attributes:
    host: 嵌入模型服务主机地址。
    port: 嵌入模型服务端口号。
    model: 使用的嵌入模型名称。
"""
@dataclass
class EmbeddingConfig:
    host: str
    port: int
    model: str
    base_url: str
    api_key: str
    batch_size: int = 32

"""
Elasticsearch 搜索服务连接配置。

Attributes:
    host: ES 服务主机地址。
    port: ES 服务端口号。
    index_name: 默认操作的索引名称。
"""
@dataclass
class ESConfig:
    host: str
    port: int
    index_name: str

"""
大语言模型 API 调用配置。

Attributes:
    model_name: 模型名称标识。
    api_key: API 认证密钥。
    base_url: API 服务基础地址。
"""
@dataclass
class LLMConfig:
    model_name: str
    api_key: str
    base_url: str

"""
全局应用配置聚合，整合所有子模块配置。

Attributes:
    logging: 日志系统配置。
    db_meta: 元数据库连接配置。
    db_dw: 数据仓库连接配置。
    qdrant: Qdrant 向量数据库配置。
    embedding: 嵌入模型服务配置。
    es: Elasticsearch 搜索服务配置。
    llm: 大语言模型 API 配置。
"""
@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta: DBConfig
    db_dw: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: ESConfig
    llm: LLMConfig

"""全局配置缓存变量，单例模式持有已加载的配置对象。"""
_CONFIG: AppConfig | None = None


def _load_dotenv() -> None:
    """加载项目根目录下的 .env 文件（若存在）。

    依次尝试 Python 项目根目录（含 pyproject.toml 的目录）与其上级目录，
    用于在本地开发时注入数据库密码、LLM API Key 等敏感配置。
    .env 不纳入版本控制，仓库中只保留 .env.example 作为模板。
    """
    project_root = Path(__file__).resolve().parents[2]
    candidates = [project_root / ".env", project_root.parent / ".env"]

    for env_file in candidates:
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # 已存在的环境变量优先，避免覆盖外部注入的配置
            os.environ.setdefault(key, value)
        break


def _resolve_env_placeholders(node):
    """递归解析配置中的 ${ENV_VAR} 与 ${ENV_VAR:默认值} 占位符。

    Args:
        node: 由 PyYAML 解析出的任意配置节点（dict/list/str）。

    Returns:
        占位符已被环境变量替换后的配置结构。
    """
    pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}")

    def replace(value: str) -> str:
        def _sub(match: re.Match) -> str:
            name, default = match.group(1), match.group(2)
            return os.environ.get(name, default if default is not None else "")

        return pattern.sub(_sub, value)

    if isinstance(node, dict):
        return {k: _resolve_env_placeholders(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_env_placeholders(v) for v in node]
    if isinstance(node, str):
        return replace(node)
    return node


def load_config() -> AppConfig:
    """
    加载并缓存应用配置。

    采用单例模式，首次调用时从 YAML 文件加载配置，
    用环境变量（含 .env 文件）替换其中的 ${ENV_VAR} 占位符，
    再与 dataclass schema 合并做类型校验，
    从而保证任何真实的密码、密钥都不会写入版本库。

    注意：这里使用 PyYAML 而非 OmegaConf 读取文件，
    因为 ${VAR} 与 OmegaConf 自身的插值语法冲突。

    Returns:
        AppConfig: 类型安全的应用全局配置对象。

    Raises:
        FileNotFoundError: 配置文件不存在。
        OmegaConf.Error: 配置与 schema 合并失败或类型转换失败。
    """
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG

    config_file = Path(__file__).resolve().parent / "app_config.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")

    # 先加载 .env，再解析占位符，使本地敏感配置不落入仓库
    _load_dotenv()

    with config_file.open(encoding="utf-8") as fp:
        raw = yaml.safe_load(fp) or {}

    resolved = _resolve_env_placeholders(raw)

    schema = OmegaConf.structured(AppConfig)
    merged = OmegaConf.merge(schema, OmegaConf.create(resolved))
    _CONFIG = OmegaConf.to_object(merged)
    return _CONFIG


"""模块加载时自动初始化并暴露全局配置单例。"""
app_config = load_config()
