from contextvars import ContextVar

"""请求级上下文变量模块。

以 ContextVar 保存当前请求的 request_id，使日志、业务代码在并发场景下
能够独立、准确地获取到属于「自己这个请求」的追踪标识。
"""

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="1")
