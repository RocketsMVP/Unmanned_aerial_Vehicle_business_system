import os
import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy import text, select
from alembic.config import Config
from alembic import command
from sqlalchemy.exc import OperationalError, ProgrammingError
from core.intra import config as viper_config

# 根级 Alembic 脚本目录（项目根下的 "alembic" 文件夹）
ALEMBIC_ROOT = os.path.join(os.getcwd(), "alembic")

# 全局连接对象
async_engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker[AsyncSession]] = None


def get_dsn(config: dict, db_type: str) -> str:
    """构建数据库连接 DSN"""
    if db_type == 'mysql':
        return (
            f"mysql+aiomysql://{config['username']}:{config['password']}@"
            f"{config['host']}:{config['port']}/{config['dbname']}?charset=utf8mb4"
        )
    else:  # postgres
        return (
            f"postgresql+asyncpg://{config['username']}:{config['password']}@"
            f"{config['host']}:{config['port']}/{config['dbname']}"
        )


async def create_database(dsn: str, dbname: str, db_type: str, timezone: str = 'Asia/Shanghai') -> None:
    """创建数据库并设置时区"""
    if db_type == 'mysql':
        # 拆分连接参数
        host = dsn.split('@')[1].split(':')[0]
        port = int(dsn.split('@')[1].split(':')[1].split('/')[0])
        user = dsn.split('://')[1].split(':')[0]
        password = dsn.split('://')[1].split(':')[1].split('@')[0]

        # 连接到 MySQL 系统库（不指定数据库）
        system_conn = await create_async_engine(
            f"mysql+aiomysql://{user}:{password}@{host}:{port}/",
            pool_size=1, max_overflow=0
        ).connect()

        try:
            # 转义数据库名（处理特殊字符如连字符）
            escaped_dbname = f"`{dbname}`" if '-' in dbname else dbname
            await system_conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {escaped_dbname}"))
            logging.getLogger("sqlalchemy").info(f"创建数据库 '{dbname}' 成功")
            # 设置时区（可选，MySQL 需要先加载时区表）
            try:
                await system_conn.execute(text(f"SET GLOBAL time_zone = '{timezone}'"))
            except Exception as e:
                logging.getLogger("sqlalchemy").warning(f"时区设置失败（不影响运行）: {e}")
        except ProgrammingError as e:
            logging.getLogger("sqlalchemy").error(f"创建数据库失败: {str(e)}")
            raise
        finally:
            await system_conn.close()

    elif db_type == 'postgres':
        # 连接到 postgres 系统库
        system_dsn = dsn.rsplit('/', 1)[0] + '/postgres'
        system_engine = create_async_engine(system_dsn, pool_size=1, max_overflow=0)
        async with system_engine.connect() as system_conn:
            await system_conn.execute(text(f"CREATE DATABASE {dbname}"))
            await system_conn.execute(text(f"ALTER DATABASE {dbname} SET timezone TO '{timezone}'"))
            logging.getLogger("sqlalchemy").info(f"创建数据库 '{dbname}' 成功")


async def init_database() -> None:
    """初始化数据库连接（支持自动创建数据库）"""
    global async_engine, AsyncSessionLocal

    db_type = viper_config.get('system.database')
    config = viper_config.get(db_type)
    dsn = get_dsn(config, db_type)

    # 配置连接池参数
    pool_config = {
        "max_overflow": config.get('max-idle-conns', 1),
        "pool_size": config.get('max-open-conns', 10),
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_use_lifo": True,  # 优先使用最近使用的连接（减少空闲连接）
        "pool_reset_on_return": "rollback",  # 连接归还时强制回滚（避免隐性事务残留）
        "connect_args": {
            "charset": "utf8mb4",
            "use_unicode": True,
            "autocommit": True,
        }

    }

    # 创建异步引擎

    try:
        # 测试连接
        async_engine = create_async_engine(dsn, **pool_config)
        async with async_engine.connect() as conn:
            await conn.scalar(select(1))
    except OperationalError as e:
        logging.getLogger("sqlalchemy").error(f"数据库连接失败: {str(e)}")
        if "Unknown database" in str(e) or "does not exist" in str(e):
            await create_database(dsn, config['dbname'], db_type)
            # 重新创建引擎（确保使用新数据库）
            async_engine = create_async_engine(dsn, **pool_config)
        else:
            raise e

    # 创建会话工厂
    AsyncSessionLocal = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    setup_logger(config)
    logging.getLogger("sqlalchemy").info("数据库连接初始化完成")
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)  # 可以设为 DEBUG 获取更详细的引擎日志
    logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)  # DEBUG 级别可以看到连接的获取和回收


def setup_logger(config: dict) -> None:
    """
    配置日志模块，设置文件和控制台处理器，并按照配置设置日志级别
    """
    log_mode = config.get('log-mode', 'info').lower()
    logger = logging.getLogger("sqlalchemy")
    logger.propagate = False
    level = logging.INFO
    if log_mode == 'debug':
        level = logging.DEBUG

    logger.setLevel(level)
    logging.getLogger('db_client').setLevel(level)

    # 清理已有的处理器，避免重复添加
    logger.handlers.clear()

    # 获取文件处理器（假设 zap.get_write_syncer 返回的是一个文件处理器列表）
    from core.intra.zap import zap
    file_handlers = zap.get_write_syncer('log/sqlalchemy.log')

    # 获取统一的日志格式器
    formatter = zap.get_encoder()

    # 配置并添加处理器
    for fh in file_handlers:
        fh.setFormatter(formatter)
        fh.setLevel(level)
        logger.addHandler(fh)


async def init_source(*initializers) -> None:
    """
    批量执行数据初始化：
    - 对于每个 initializer，先调用 check_data_exist(session)
    - 若返回 False，则调用 initialize(session)
    - 全部在同一个事务中提交

    参数：
    - SessionLocal: 通过 get_engine_and_session() 返回的 async_sessionmaker
    - initializers: 任意实现了异步方法
        * check_data_exist(session: AsyncSession) -> bool
        * initialize(session: AsyncSession) -> None
    """
    for initializer in initializers:
        # 调用用户实现的检查方法
        exists = await initializer.check_data_exist()
        if not exists:
            # 调用用户实现的初始化方法
            await initializer.initialize()


async def run_module_migrations():
    """
    对多个模块分别进行 Alembic 自动迁移
    """
    db_type = viper_config.get("system.database")
    cfg = viper_config.get(db_type)
    engine_url = get_dsn(cfg, db_type)
    engine_url = engine_url.replace("aiomysql", "pymysql")
    alembic_cfg = Config()
    versions_dir = os.path.join(ALEMBIC_ROOT, "versions")
    os.makedirs(versions_dir, exist_ok=True)

    alembic_cfg.set_main_option("script_location", ALEMBIC_ROOT)
    alembic_cfg.set_main_option("sqlalchemy.url", engine_url)
    alembic_cfg.set_main_option("version_locations", versions_dir)
    try:
        command.check(alembic_cfg)
        logging.info("模型与数据库 schema 一致，无需迁移。")
        return
    except command.util.CommandError as e:
        print(e)
        if "New upgrade operations detected" in str(e):
            logging.info("数据库 schema 不一致，开始迁移...")
            command.revision(alembic_cfg, message="autogen_all_modules", autogenerate=True)
            command.upgrade(alembic_cfg, "head")
        elif "Target database is not up to date" in str(e):
            logging.info("先将数据库升级到最新 head...")
            command.stamp(alembic_cfg, "head")
            command.revision(alembic_cfg, message="autogen_all_modules", autogenerate=True)
            command.upgrade(alembic_cfg, "head")
        elif "Multiple heads" in str(e):
            logging.warning("检测到多个迁移heads，尝试自动创建表...")
            # 遇到多heads问题时，直接创建表
    except Exception as e:
        command.downgrade(alembic_cfg, "")
        latest_migration = max([f for f in os.listdir(versions_dir) if f.endswith(".py")],
                               key=lambda x: os.path.getmtime(os.path.join(versions_dir, x)))
        migration_path = os.path.join(versions_dir, latest_migration)
        if os.path.exists(migration_path):
            os.remove(migration_path)
        logging.error(f"Failed to migrate module: {e}")
        raise e
