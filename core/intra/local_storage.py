import os
from datetime import datetime
from io import BytesIO

from core.intra import zap
from core.intra.viper import config


class LocalStorage:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalStorage, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 初始化本地存储，获取基础目录配置
        self.base_dir = config.get_string('system.data-dir', './data_dir')
        self._initialized = True

    def _build_path(self, file_name: str, file_type: str) -> str:
        """
        构建存储路径：{base_dir}/document/{文件类型}/{年}/{月}/{日}/{文件名}
        文件名应该已经是MD5格式，不使用原文件名
        :param file_name: 文件名（应该是MD5格式）
        :param file_type: 文件类型（如 "pdf", "jpg"）
        :return: 完整路径
        """
        # 生成基于日期的路径
        date_path = datetime.now().strftime("%Y/%m/%d")  # 例如 "2025/01/15"
        # 构建完整路径：{base_dir}/document/{文件类型}/{年}/{月}/{日}/{文件名}
        full_path = os.path.join(self.base_dir, "document", file_type, date_path, file_name)
        return full_path

    def save_file(self, file_name: str, file_content: bytes, file_type: str) -> str:
        """
        保存文件到本地存储
        :param file_name: 文件名（不包含路径）
        :param file_content: 文件内容
        :param file_type: 文件类型（如 "pdf", "jpg"）
        :return: 存储的完整路径
        """
        try:
            # 构建完整路径
            full_path = self._build_path(file_name, file_type)
            
            # 确保目录存在
            directory = os.path.dirname(full_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True, mode=0o755)

            # 保存文件
            with open(full_path, 'wb') as f:
                f.write(file_content)
            return full_path
        except Exception as e:
            zap.logger.error(f"保存文件 {file_name} 时出错: {e}")
            raise

    def read_file(self, object_name: str) -> bytes:
        """
        从本地存储读取文件
        :param object_name: 存储的对象名称
        :return: 文件内容
        """
        try:
            if not os.path.exists(object_name):
                raise FileNotFoundError(f"文件不存在: {object_name}")
            with open(object_name, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise
        except Exception as e:
            zap.logger.error(f"读取文件 {object_name} 时出错: {e}")
            raise

    def delete_file(self, object_name: str) -> bool:
        """
        删除本地存储中的文件
        :param object_name: 存储的对象名称
        :return: 是否删除成功
        """
        try:
            os.remove(object_name)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            zap.logger.error(f"删除文件 {object_name} 时出错: {e}")
            return False

    def get_put_url(self, object_name: str) -> None:
        """
        本地存储不支持预签名URL
        :param object_name: 存储的对象名称
        :return: None
        """
        return None

