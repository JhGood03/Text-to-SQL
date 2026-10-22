import asyncio
from typing import Optional
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.conf.app_config import DBConfig, app_config

class MysqlClientManager:
    """异步 MySQL 客户端管理器，封装连接引擎的创建、关闭及会话工厂的初始化。"""

    def __init__(self, db_config: DBConfig):
        """
        初始化 MySQL 客户端管理器。

        Args:
            db_config: 数据库连接配置，包含 host、port、user、password、database 等信息。
        """
        self.db_config = db_config
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[sessionmaker] = None

    def _get_url(self):
        """
        构建带 URL 编码密码的异步 MySQL 连接 URL。

        Returns:
            符合 SQLAlchemy 异步引擎要求的连接字符串。
        """
        return (f"mysql+asyncmy://{self.db_config.user}:{quote_plus(self.db_config.password)}"
                f"@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}?charset=utf8mb4")

    def init(self):
        """
        初始化异步引擎与会话工厂。

        若引擎已存在，先异步释放旧引擎再创建新连接，避免重复初始化导致连接池泄漏。
        """
        if self.engine is not None:
            import asyncio
            asyncio.create_task(self.engine.dispose())
        self.engine = create_async_engine(url=self._get_url(),
                                          pool_size=10,
                                          pool_pre_ping=True)
        self.session_factory = async_sessionmaker(self.engine,
                                                  autoflush=True,
                                                  expire_on_commit=False,
                                                  autobegin=True)

    async def close(self):
        """关闭异步引擎，释放连接池资源。"""
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None

dw_mysql_client_manager = MysqlClientManager(app_config.db_dw)
meta_mysql_client_manager = MysqlClientManager(app_config.db_meta)

if __name__ == '__main__':
    # 测试入口：初始化客户端并执行查询验证连接是否正常
    dw_mysql_client_manager.init()
    Session = dw_mysql_client_manager.session_factory
    async def test():
        async with Session() as session:
            sql = text("select * from dim_product limit 3")
            result = await session.execute(sql)
            rows = result.fetchall()
            print(rows)

    asyncio.run(test())
