"""日志工具：把子进程日志通过队列转发到 UI。"""
import time


class LogRecord:
    __slots__ = ("time", "level", "message")

    def __init__(self, level, message):
        self.time = time.strftime("%H:%M:%S")
        self.level = level
        self.message = message


def format_record(record: LogRecord) -> str:
    return f"[{record.time}] {record.message}"
