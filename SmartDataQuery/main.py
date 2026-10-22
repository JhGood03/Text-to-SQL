import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers.query_router import query_router
from app.core.context import request_id_ctx_var
from app.core.lifespan import lifespan

app = FastAPI(lifespan=lifespan)

# 前端静态资源目录（单页面应用）
STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """为每个请求生成唯一的 request_id 并写入上下文变量。

    Args:
        request: 当前 HTTP 请求。
        call_next: 下游处理函数。

    Returns:
        下游返回的响应对象。
    """
    # 调用路径函数之前
    request_id = str(uuid.uuid4())
    request_id_ctx_var.set(request_id)
    # 调用路径函数
    response = await call_next(request)
    # 调用路径函数之后
    response.headers["X-Request-ID"] = request_id
    return response


# 注册路由
app.include_router(query_router)


@app.get("/", include_in_schema=False)
async def index():
    """返回问数页面。

    Returns:
        index.html 的静态文件响应。
    """
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


# 挂载静态资源，放在路由注册之后，避免抢占 /api 前缀
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main():
    print("Hello from smartdataquery!")


if __name__ == "__main__":
    main()
