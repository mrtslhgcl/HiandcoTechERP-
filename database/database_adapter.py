import sqlite3
import os
import json
import threading


class DatabaseAdapter:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._base_dir = os.environ.get('HIANDCO_BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._app_dir = os.environ.get('HIANDCO_APP_DIR', self._base_dir)
        self._config = self._load_config()

        self._local_conn = None
        self._local_path = None
        self._setup_local()

        self._turso = None
        self._turso_available = False
        self._last_sync_error = None
        self._bg_lock = threading.Lock()

        if self._config.get("mode") == "hybrid":
            self._setup_turso()

        self.connection = self._local_conn
        self.sync_enabled = self._turso_available


    def _load_config(self) -> dict:
        config_path = os.path.join(self._base_dir, "db_config.json")
        default = {
            "mode": "local",
            "turso_url": "",
            "turso_auth_token": "",
            "sync_interval_seconds": 300,
        }
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                for key in default:
                    if key in loaded:
                        default[key] = loaded[key]
            except Exception:
                pass
        return default


    def _setup_local(self):
        db_dir = os.path.join(self._app_dir, "data")
        os.makedirs(db_dir, exist_ok=True)
        self._local_path = os.path.join(db_dir, "app.db")

        self._local_conn = sqlite3.connect(self._local_path, check_same_thread=False)
        self._local_conn.row_factory = sqlite3.Row
        self._local_conn.execute("PRAGMA journal_mode=WAL")
        self._local_conn.execute("PRAGMA foreign_keys=ON")

        self._local_conn.execute("""
            CREATE TABLE IF NOT EXISTS _write_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                params TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        self._local_conn.commit()

    def _setup_turso(self):
        url = self._config.get("turso_url", "").strip()
        token = self._config.get("turso_auth_token", "").strip()

        if not url or not token:
            return

        try:
            from database.turso_client import TursoClient
            self._turso = TursoClient(url, token)
            if self._turso.ping():
                self._turso_available = True
                self.sync_enabled = True
                self._last_sync_error = None
            else:
                self._last_sync_error = "Turso bağlantı testi başarısız"
        except Exception as e:
            self._last_sync_error = str(e)


    def execute(self, query: str, params: tuple = ()):
        try:
            cursor = self._local_conn.execute(query, params)
            self._local_conn.commit()
        except Exception as e:
            try:
                self._local_conn.rollback()
            except Exception:
                pass
            raise e

        if self._turso_available:
            q_upper = query.strip().upper()
            if not q_upper.startswith(("SELECT", "PRAGMA")):
                self._send_to_turso_bg(query, params)
        elif self._turso is not None:
            self._queue_write(query, params)

        return cursor

    def execute_many(self, query: str, params_list: list):
        try:
            cursor = self._local_conn.cursor()
            cursor.executemany(query, params_list)
            self._local_conn.commit()
        except Exception as e:
            try:
                self._local_conn.rollback()
            except Exception:
                pass
            raise e

        if self._turso_available:
            q_upper = query.strip().upper()
            if not q_upper.startswith(("SELECT", "PRAGMA")):
                for params in params_list:
                    self._send_to_turso_bg(query, params)

        return cursor

    def fetch_one(self, query: str, params: tuple = ()) -> dict | None:
        cursor = self._local_conn.execute(query, params)
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetch_all(self, query: str, params: tuple = ()) -> list[dict]:
        cursor = self._local_conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


    def _send_to_turso_bg(self, query: str, params: tuple):
        q_upper = query.strip().upper()
        if q_upper.startswith(("SELECT", "PRAGMA")):
            return

        def _do():
            try:
                with self._bg_lock:
                    self._turso.execute(query, params)
            except ConnectionError as e:
                self._turso_available = False
                self._last_sync_error = str(e)
                self._queue_write(query, params)
            except RuntimeError:
                pass
            except Exception:
                self._queue_write(query, params)

        t = threading.Thread(target=_do, daemon=True)
        t.start()


    def _queue_write(self, query: str, params: tuple):
        from datetime import datetime

        q_upper = query.strip().upper()
        if q_upper.startswith(("SELECT", "PRAGMA", "CREATE TABLE IF NOT EXISTS")):
            return

        try:
            self._local_conn.execute(
                "INSERT INTO _write_queue (query, params, created_at) VALUES (?, ?, ?)",
                (query, json.dumps(list(params)), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            self._local_conn.commit()
        except Exception:
            pass

    def _replay_write_queue(self) -> int:
        if not self._turso_available or not self._turso:
            return 0

        try:
            cursor = self._local_conn.execute(
                "SELECT * FROM _write_queue ORDER BY id"
            )
            entries = [dict(row) for row in cursor.fetchall()]
        except Exception:
            return 0

        replayed = 0
        for entry in entries:
            try:
                params = tuple(json.loads(entry["params"]))
                self._turso.execute(entry["query"], params)
                self._local_conn.execute(
                    "DELETE FROM _write_queue WHERE id = ?", (entry["id"],)
                )
                self._local_conn.commit()
                replayed += 1
            except RuntimeError:
                self._local_conn.execute(
                    "DELETE FROM _write_queue WHERE id = ?", (entry["id"],)
                )
                self._local_conn.commit()
            except ConnectionError:
                break

        return replayed

    def get_queue_size(self) -> int:
        try:
            cursor = self._local_conn.execute("SELECT COUNT(*) FROM _write_queue")
            row = cursor.fetchone()
            return dict(row).get("COUNT(*)", 0) if row else 0
        except Exception:
            return 0


    def sync(self) -> bool:
        if not self._turso:
            return False

        if not self._turso_available:
            try:
                if self._turso.ping():
                    self._turso_available = True
                    self.sync_enabled = True
                    self._last_sync_error = None
                else:
                    return False
            except Exception:
                return False

        queued = self.get_queue_size()
        if queued > 0:
            self._replay_write_queue()

        try:
            self._pull_from_turso()
        except Exception:
            pass

        try:
            self._turso.ping()
            self._last_sync_error = None
            return True
        except Exception as e:
            self._turso_available = False
            self._last_sync_error = str(e)
            return False

    def _pull_from_turso(self):
        if not self._turso_available:
            return

        try:
            result = self._turso.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_libsql_%' "
                "AND name != '_write_queue'"
            )
            turso_tables = [r[0] for r in result.fetchall()]
        except Exception:
            return

        self._local_conn.execute("PRAGMA foreign_keys=OFF")

        for table in turso_tables:
            try:
                result = self._turso.execute(f"SELECT * FROM [{table}]")
                columns = [desc[0] for desc in result.description]
                turso_rows = result.fetchall()

                if not turso_rows or not columns:
                    continue

                col_str = ", ".join(columns)
                placeholders = ", ".join(["?" for _ in columns])

                for row in turso_rows:
                    try:
                        self._local_conn.execute(
                            f"INSERT OR REPLACE INTO {table} ({col_str}) VALUES ({placeholders})",
                            row,
                        )
                    except Exception:
                        pass

            except Exception:
                pass

        try:
            self._local_conn.commit()
            self._local_conn.execute("PRAGMA foreign_keys=ON")
        except Exception:
            pass


    def _sort_tables_by_deps(self, tables: list) -> list:
        import re

        table_dict = {name: sql for name, sql in tables}
        table_names = set(table_dict.keys())

        deps = {}
        for name, sql in tables:
            refs = set()
            if sql:
                matches = re.findall(r'REFERENCES\s+["\']?(\w+)["\']?', sql, re.IGNORECASE)
                for ref in matches:
                    if ref in table_names and ref != name:
                        refs.add(ref)
            deps[name] = refs

        sorted_list = []
        visited = set()
        remaining = set(table_names)

        max_iter = len(table_names) + 1
        iteration = 0

        while remaining and iteration < max_iter:
            iteration += 1
            ready = []
            for name in remaining:
                unmet = deps.get(name, set()) - visited
                if not unmet:
                    ready.append(name)

            if not ready:
                ready = sorted(remaining)

            for name in sorted(ready):
                sorted_list.append(name)
                visited.add(name)
                remaining.discard(name)

        return [(name, table_dict[name]) for name in sorted_list]


    def migrate_local_to_turso(self) -> bool:
        if not self._turso_available or not self._turso:
            return False

        try:
            turso_has_data = False
            try:
                result = self._turso.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_libsql_%' "
                    "AND name != '_write_queue'"
                )
                turso_tables = [r[0] for r in result.fetchall()]
                for table in turso_tables:
                    try:
                        r = self._turso.execute(f"SELECT COUNT(*) FROM {table}")
                        row = r.fetchone()
                        if row and row[0] > 0:
                            turso_has_data = True
                            break
                    except Exception:
                        pass
            except Exception:
                turso_tables = []

            if turso_has_data:
                return False

            cursor = self._local_conn.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' AND name != '_write_queue' "
                "AND sql IS NOT NULL ORDER BY name"
            )
            local_tables = [(dict(row)["name"], dict(row)["sql"]) for row in cursor.fetchall()]

            if not local_tables:
                return False

            try:
                self._turso.execute("PRAGMA foreign_keys=OFF")
            except Exception:
                pass

            for table_name, create_sql in local_tables:
                if not create_sql:
                    continue
                safe_sql = create_sql.replace(
                    "CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ", 1
                )
                try:
                    self._turso.execute(safe_sql)
                except RuntimeError:
                    pass
                except Exception:
                    pass

            sorted_tables = self._sort_tables_by_deps(local_tables)

            for table_name, _ in sorted_tables:
                try:
                    cursor = self._local_conn.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    if not rows:
                        continue

                    columns = [desc[0] for desc in cursor.description]
                    col_str = ", ".join(columns)
                    placeholders = ", ".join(["?" for _ in columns])

                    statements = []
                    for row in rows:
                        values = tuple(row)
                        statements.append((
                            f"INSERT OR REPLACE INTO {table_name} ({col_str}) VALUES ({placeholders})",
                            values,
                        ))

                    for i in range(0, len(statements), 50):
                        batch = statements[i:i + 50]
                        try:
                            self._turso.execute_batch(batch)
                        except Exception:
                            pass

                except Exception:
                    pass

            try:
                self._turso.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass

            return True

        except Exception:
            try:
                self._turso.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass
            return False


    @property
    def is_online(self) -> bool:
        return self._turso_available and self._last_sync_error is None

    @property
    def mode(self) -> str:
        if self._turso is not None:
            return "hybrid"
        return "local"

    @property
    def sync_interval(self) -> int:
        return self._config.get("sync_interval_seconds", 300)

    @property
    def connection_info(self) -> dict:
        return {
            "mode": self.mode,
            "is_online": self.is_online,
            "sync_enabled": self.sync_enabled,
            "turso_available": self._turso_available,
            "last_error": self._last_sync_error,
            "queue_size": self.get_queue_size(),
        }

    def close(self):
        if self._local_conn:
            if self._turso_available:
                self.sync()
            self._local_conn.close()
            self._local_conn = None
            self.connection = None
            DatabaseAdapter._instance = None
            self._initialized = False
