import importlib
import os.path

from fastapi import FastAPI


from core.intra import config

module_env = {}


async def initialize_module():
    # 1. 读取配置，增加默认值处理
    addons_path_str = config.get("system.addons-path")
    if not addons_path_str:
        return
    addons_paths = [path.strip() for path in addons_path_str.split(",") if path.strip()]

    for ad in addons_paths:
        real_path = os.path.normcase(os.path.abspath(ad))

        # 2. 检查路径有效性
        if not os.path.exists(real_path):
            continue

        # 遍历 system_layer 下的模块
        for module_dir in os.listdir(real_path):
            module_full_path = os.path.join(real_path, module_dir)
            # 检查是否是目录且包含 __init__.py（标识为 Python 模块）
            if os.path.isdir(module_full_path) and os.path.exists(os.path.join(module_full_path, "__init__.py")):
                try:
                    # 构建导入路径：core.app.system_layer.模块名
                    module_name = f"{ad.replace('/', '.')}.{module_dir}"

                    module = importlib.import_module(module_name)
                    module_env[module_name] = module
                except ImportError as e:
                    print(f"模块 {module_dir} 导入失败，错误：{e}")
                    raise e
    from core import run_module_migrations
    await run_module_migrations()
    # 可扩展：如果模块有初始化函数，调用它
    for key in module_env:
        module = module_env[key]
        if hasattr(module, "init"):
            await module.init()


"""
    暂时废弃自动化加载路由和数据库模型
    后续考虑增加自动生成数据库模型的功能
"""


def include_all_routers(app: FastAPI, package: str, directory: str):
    """
    遍历指定目录下的所有 .py 文件，自动导入并注册其中名为 router 或 user_router 的路由对象
    """
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            full_module_name = f"{package}.{module_name}"
            module = importlib.import_module(full_module_name)

            # 根据命名习惯获取路由对象（例如 router 或 user_router）
            if hasattr(module, "router"):
                app.include_router(getattr(module, "router"))
            elif hasattr(module, "user_router"):
                app.include_router(getattr(module, "user_router"))


def include_all_db(package: str, directory: str):
    """
    遍历指定目录下的所有 .py 文件，自动导入并注册到数据库中
    """
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            full_module_name = f"{package}.{module_name}"
            module = importlib.import_module(full_module_name)
            print(module)
            #
            # # 根据命名习惯获取路由对象（例如 router 或 user_router）
            # if hasattr(module, "models"):
            #     app.include_router(getattr(module, "router"))
            # elif hasattr(module, "user_router"):
            #     app.include_router(getattr(module, "user_router"))
