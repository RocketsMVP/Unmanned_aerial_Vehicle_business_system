import os
import logging
from logging.handlers import RotatingFileHandler
import time
import json

from core.intra import config


class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'


class LevelFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno == self.level


class Zap:
    def __init__(self):
        self.logger = None
        self.setup_logging()

    def create_dir(self, director):
        if not os.path.exists(director):
            os.makedirs(director, exist_ok=True)

    def custom_time_encoder(self, record, datefmt=None):
        prefix = config.get("zap.prefix") or ""
        return time.strftime(f"{prefix}%Y/%m/%d - %H:%M:%S", time.localtime(record.created))

    def get_encoder(self):

        log_format = config.get("zap.format")
        if log_format == "json":
            # JSON 模式：保留一个 plain-text 可点击字段 caller_link
            fmt = (
                '{"time":"%(asctime)s","level":"%(levelname)s",'
                '"message":"%(message)s","caller":"%(pathname)s:%(lineno)d:%(funcName)s",'
                '"caller_link":"%(pathname)s:%(lineno)d"}'
            )
        else:
            fmt = '%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:%(funcName)s - %(message)s'
        formatter = logging.Formatter(fmt)
        formatter.formatTime = self.custom_time_encoder
        return formatter

    def get_write_syncer(self, file):
        file_handler = RotatingFileHandler(
            filename=file,
            maxBytes=10 * 1024 * 1024,
            backupCount=30,
            encoding='utf-8'
        )
        handlers = [file_handler]
        log_in_console = config.get("zap.log-in-console")
        if log_in_console:
            handlers.append(logging.StreamHandler())
        return handlers

    def setup_logging(self):
        director = config.get("zap.director") or "./log"
        self.create_dir(director)

        self.logger = logging.getLogger()
        # 清除现有处理器
        for h in list(self.logger.handlers):
            self.logger.removeHandler(h)
        self.logger.propagate = False

        log_level = (config.get("zap.level") or "DEBUG").upper()
        self.logger.setLevel(log_level)

        log_levels = {
            logging.DEBUG: os.path.join(director, "debug.log"),
            logging.INFO: os.path.join(director, "info.log"),
            logging.WARNING: os.path.join(director, "warn.log"),
            logging.ERROR: os.path.join(director, "error.log")
        }

        formatter = self.get_encoder()

        for level, file in log_levels.items():
            handlers = self.get_write_syncer(file)
            for handler in handlers:
                handler.setLevel(level)
                handler.addFilter(LevelFilter(level))
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)


# 单例
zap = Zap()
