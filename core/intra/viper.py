import argparse
import logging
import os
import time
from typing import Any

import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 禁用 watchdog 的日志输出
logging.getLogger('fsevents').setLevel(logging.CRITICAL)


class ConfigFileHandler(FileSystemEventHandler):
    def __init__(self, config_path: str):
        self.config_path = os.path.abspath(config_path)
        self._last_modified_time = 0

    def on_modified(self, event):
        # 只处理 config 文件的事件
        if os.path.abspath(event.src_path) != self.config_path:
            return
        try:
            current_time = time.time()
            # 避免重复加载，间隔 1 秒以上才加载
            if current_time - self._last_modified_time > 1:
                # 重新加载配置
                config.load_viper()  # 假设这里会更新全局配置
                self._last_modified_time = current_time
                print("配置文件已更新，重新加载成功")
        except Exception as e:
            print(f"重新加载配置文件时出错: {e}")


class Config:
    def __init__(self):
        self.config = ""
        self._observer = None
        self._last_modified_time = 0
        self.load_viper()

    def load_viper(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', type=str, default='', help='choose config file')
        args = parser.parse_args()
        if not args.c:
            config_env = os.getenv('CONFIG')
            if not config_env:
                config_file_prefix = 'config'
                config_path = f'./{config_file_prefix}.yaml'
                print(f"当前使用的为config默认值，config路径为{config_path}")
            else:
                config_path = config_env
                print(f"当前使用的为CONFIG环境变量，config路径为{config_path}")
        else:
            config_path = args.c
            print(f"当前使用命令行的-c参数传递的值，config路径为{config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
            # 启动文件监听
            self.start_watching(config_path)
        except FileNotFoundError:
            raise ValueError(f"加载配置文件错误：文件 {config_path} 未找到")
        except yaml.YAMLError as e:
            raise ValueError(f"加载配置文件错误：{e}")

    def start_watching(self, file_path):
        if self._observer is None:
            event_handler = ConfigFileHandler(file_path)
            self._observer = Observer()
            self._observer.schedule(event_handler, path=os.path.dirname(file_path), recursive=False)
            self._observer.start()

    def get(self, key, default=None) -> Any:
        keys = key.split('.')
        value = self.config
        for key in keys:
            if key in value:
                value = value[key]
            else:
                return default
        return value

    def get_string(self, key, default=''):
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_int(self, key, default=0):
        value = self.get(key, default)
        return int(value) if value is not None else default

    def get_float(self, key, default=0.0):
        value = self.get(key, default)
        return float(value) if value is not None else default

    def get_bool(self, key, default=False):
        value = self.get(key, default)
        return bool(value) if value is not None else default

    def get_list(self, key, default=None):
        if default is None:
            default = []
        value = self.get(key, default)
        return list(value) if value is not None else default

    def get_dict(self, key, default=None):
        if default is None:
            default = {}
        value = self.get(key, default)
        return dict(value) if value is not None else default


config = Config()
