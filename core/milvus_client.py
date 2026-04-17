"""
Milvus 向量数据库客户端。

当前为懒加载占位符，仅在首次访问时抛出提示。
后续需连接真实的 Milvus 服务（默认 127.0.0.1:19530）。
"""

from core.intra import config


class _MilvusClientProxy:
    """懒加载代理：仅在首次访问时提示未配置"""

    def __getattr__(self, name):
        milvus_config = config.get("milvus")
        if milvus_config is None:
            raise RuntimeError(
                "Milvus client accessed but not configured. "
                "Milvus is not yet implemented in this project. "
                "Add milvus config to config.yaml and implement core/milvus_client.py "
                "if you need vector search / RAG capabilities."
            )
        # 未来实现：在此初始化真正的 Milvus 客户端
        raise NotImplementedError(
            f"Milvus client method '{name}' not yet implemented."
        )


milvus_client = _MilvusClientProxy()
