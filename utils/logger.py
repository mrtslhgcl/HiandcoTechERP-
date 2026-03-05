import os
import json
from datetime import datetime, date

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._logs_dir = os.path.join(os.environ.get('HIANDCO_APP_DIR', os.environ.get('HIANDCO_BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "logs")
        os.makedirs(self._logs_dir, exist_ok=True)

    def _get_log_file_path(self):
        filename = f"{date.today().strftime('%Y-%m-%d')}.log"
        return os.path.join(self._logs_dir, filename)

    def _write(self, level: str, user: str, source: str, message: str, details: dict = None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        details_str = f" - {json.dumps(details, ensure_ascii=False)}" if details else ""
        log_line = f"[{timestamp}] [{level}] [{user}] [{source}] {message}{details_str}\n"

        with open(self._get_log_file_path(), "a", encoding="utf-8") as f:
            f.write(log_line)

    def info(self, user: str, source: str, message: str, details: dict = None):
        self._write("INFO", user, source, message, details)

    def warning(self, user: str, source: str, message: str, details: dict = None):
        self._write("WARNING", user, source, message, details)

    def error(self, user: str, source: str, message: str, details: dict = None):
        self._write("ERROR", user, source, message, details)

    def critical(self, user: str, source: str, message: str, details: dict = None):
        self._write("CRITICAL", user, source, message, details)

    def debug(self, user: str, source: str, message: str, details: dict = None):
        self._write("DEBUG", user, source, message, details)

    def get_logs(self, target_date: date = None) -> list[str]:
        if target_date is None:
            target_date = date.today()

        filename = f"{target_date.strftime('%Y-%m-%d')}.log"
        filepath = os.path.join(self._logs_dir, filename)

        if not os.path.exists(filepath):
            return []

        with open(filepath, "r", encoding="utf-8") as f:
            return f.readlines()

    def get_available_dates(self) -> list[date]:
        dates = []
        for filename in os.listdir(self._logs_dir):
            if filename.endswith(".log"):
                try:
                    d = datetime.strptime(filename.replace(".log", ""), "%Y-%m-%d").date()
                    dates.append(d)
                except ValueError:
                    continue
        dates.sort(reverse=True)
        return dates

    def delete_logs(self, start_date: date, end_date: date) -> int:
        deleted_count = 0
        for filename in os.listdir(self._logs_dir):
            if filename.endswith(".log"):
                try:
                    file_date = datetime.strptime(filename.replace(".log", ""), "%Y-%m-%d").date()
                    if start_date <= file_date <= end_date:
                        os.remove(os.path.join(self._logs_dir, filename))
                        deleted_count += 1
                except ValueError:
                    continue
        return deleted_count