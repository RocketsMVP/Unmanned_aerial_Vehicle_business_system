import json
import os
from datetime import timedelta, datetime
from io import BytesIO

from minio import Minio
from minio.datatypes import PostPolicy

from core.intra.viper import config


class MinioStorage:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MinioStorage, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._init_client()
        self.bucket_name = config.get_string("minio.bucket-name")
        # 外部访问地址（用于生成可公开访问的 URL）
        self.external_access = config.get_string("minio.external-access") or ""
        self._initialized = True

    def _init_client(self):
        """初始化 MinIO 客户端（内部连接）"""
        self.client = Minio(
            endpoint=f"{config.get_string('minio.host')}:{config.get_string('minio.port')}",
            access_key=config.get_string("minio.username"),
            secret_key=config.get_string("minio.password"),
            secure=False,
        )
        bucket_name = config.get_string("minio.bucket-name")
        found = self.client.bucket_exists(bucket_name=bucket_name)
        if not found:
            self.client.make_bucket(bucket_name=bucket_name)
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadNoList",
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
                    }
                ],
            }
            policy_json = json.dumps(policy)
            self.client.set_bucket_policy(bucket_name=bucket_name, policy=policy_json)
            print("Created bucket", bucket_name)
        else:
            print("Bucket", bucket_name, "already exists")

    def save_file(self, file_name: str, file_content: bytes, file_type: str) -> str:
        """
        保存文件到 MinIO
        :param file_name: 存储的文件名
        :param file_content: 文件内容
        :param file_type: 文件类型（仅用于对齐接口，MinIO 中不需要）
        :return: 外部可访问的文件 URL
        """
        # 使用 BytesIO 作为文件对象
        file_data = BytesIO(file_content)
        file_length = len(file_content)
        date_path = datetime.now().strftime("%Y/%m/%d")  # 例如 "2025/01/15"
        # 构建完整路径：{base_dir}/document/{文件类型}/{年}/{月}/{日}/{文件名}
        full_path = os.path.join(file_type, date_path, file_name)

        # 上传文件
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=full_path,
            data=file_data,
            length=file_length,
        )

        # 返回外部可访问的 URL
        return f"http://{self.external_access}/{self.bucket_name}/{full_path}"

    def read_file(self, object_name: str) -> bytes:
        """
        从 MinIO 下载文件
        :param object_name: 存储的对象名称
        :return: 文件内容
        """
        response = self.client.get_object(
            bucket_name=self.bucket_name, object_name=object_name
        )
        content = response.read()
        response.close()
        response.release_conn()

        return content

    def delete_file(self, object_name: str) -> bool:
        """
        从 MinIO 删除文件
        :param object_name: 存储的对象名称
        :return: 是否删除成功
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name, object_name=object_name
            )
            return True
        except Exception as e:
            print(f"删除文件 {object_name} 时出错: {e}")
            return False

    def get_put_url(self, object_name: str) -> str:
        """
        获取预签名的 PUT URL（外部可访问地址）
        :param object_name: 存储的对象名称
        :return: 预签名的 PUT URL
        """
        # 先获取内部签名的 URL
        internal_url = self.client.presigned_put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            expires=timedelta(hours=1),
        )
        # 替换内部地址为外部访问地址
        internal_endpoint = (
            f"{config.get_string('minio.host')}:{config.get_string('minio.port')}"
        )
        external = self.external_access.rstrip("/")
        return internal_url.replace(internal_endpoint, external)

    def get_upload_policy(self, prefix: str = "uploads/") -> dict:
        """
        生成一个允许上传任意文件名的策略（通常限制在某个文件夹下）
        :param prefix: 限制只能上传到哪个文件夹，例如 "uploads/"。留空则不限制。
        :return: 表单数据
        """
        # 创建策略，设置有效期
        policy = PostPolicy(self.bucket_name, datetime.utcnow() + timedelta(hours=1))

        # 设置文件名限制
        # "starts-with" 表示：允许上传的文件名必须以 prefix 开头
        # 如果 prefix 是空字符串 ""，则表示允许上传任意文件名的文件
        policy.add_starts_with_condition("key", prefix)

        # (可选) 限制文件大小，例如 1MB - 10MB
        policy.add_content_length_range_condition(1024 * 1024, 10 * 1024 * 1024)

        # 生成表单数据
        form_data = self.client.presigned_post_policy(policy)

        return form_data


class _MinioClientProxy:
    """懒加载代理：仅在首次访问时初始化 MinIO 客户端"""

    def __getattr__(self, name):
        storage_type = config.get_string("system.storage-type")
        if storage_type != "minio":
            raise RuntimeError(
                f"MinIO client accessed but storage-type is '{storage_type}', not 'minio'. "
                "Set system.storage-type to 'minio' in config.yaml to enable MinIO storage."
            )
        # 初始化真正的客户端
        _client = MinioStorage()
        # 替换自身为真实实例，后续访问直接走实例
        self.__class__ = _client.__class__
        self.__dict__.update(_client.__dict__)
        return getattr(_client, name)


minio_client = _MinioClientProxy()
