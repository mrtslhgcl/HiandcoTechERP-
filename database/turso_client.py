import json
import urllib.request
import urllib.error


class TursoResult:

    def __init__(self, result_data: dict = None):
        result_data = result_data or {}

        self.description = [
            (col["name"], None, None, None, None, None, None)
            for col in result_data.get("cols", [])
        ]

        self._rows = self._parse_rows(result_data)

        self.rowcount = result_data.get("affected_row_count", 0)

        raw_id = result_data.get("last_insert_rowid")
        self.lastrowid = int(raw_id) if raw_id is not None else None

        self._pos = 0

    def _parse_rows(self, result_data: dict) -> list:
        rows = []
        for raw_row in result_data.get("rows", []):
            row = []
            for cell in raw_row:
                cell_type = cell.get("type", "null")
                if cell_type == "null":
                    row.append(None)
                elif cell_type == "integer":
                    row.append(int(cell["value"]))
                elif cell_type == "float":
                    row.append(float(cell["value"]))
                elif cell_type == "text":
                    row.append(cell["value"])
                elif cell_type == "blob":
                    import base64
                    row.append(base64.b64decode(cell["base64"]))
                else:
                    row.append(cell.get("value"))
            rows.append(tuple(row))
        return rows

    def fetchone(self):
        if self._pos >= len(self._rows):
            return None
        row = self._rows[self._pos]
        self._pos += 1
        return row

    def fetchall(self) -> list:
        rows = self._rows[self._pos:]
        self._pos = len(self._rows)
        return rows


class TursoClient:

    def __init__(self, db_url: str, auth_token: str, timeout: int = 15):
        self.base_url = db_url.strip().replace("libsql://", "https://").rstrip("/")
        self.pipeline_url = f"{self.base_url}/v3/pipeline"
        self.auth_token = auth_token.strip()
        self.timeout = timeout


    def execute(self, sql: str, params: tuple = ()) -> TursoResult:
        args = [self._convert_param(p) for p in params]
        body = {
            "requests": [
                {"type": "execute", "stmt": {"sql": sql, "args": args}},
                {"type": "close"},
            ]
        }
        response = self._post(body)
        return self._parse_single_result(response)

    def execute_batch(self, statements: list) -> list:
        requests = []
        for sql, params in statements:
            args = [self._convert_param(p) for p in (params or ())]
            requests.append({"type": "execute", "stmt": {"sql": sql, "args": args}})
        requests.append({"type": "close"})

        body = {"requests": requests}
        response = self._post(body)
        return self._parse_batch_results(response)

    def ping(self) -> bool:
        try:
            self.execute("SELECT 1")
            return True
        except Exception:
            return False


    @staticmethod
    def _convert_param(value):
        if value is None:
            return {"type": "null"}
        elif isinstance(value, bool):
            return {"type": "integer", "value": str(int(value))}
        elif isinstance(value, int):
            return {"type": "integer", "value": str(value)}
        elif isinstance(value, float):
            return {"type": "float", "value": value}
        elif isinstance(value, str):
            return {"type": "text", "value": value}
        elif isinstance(value, bytes):
            import base64
            return {"type": "blob", "base64": base64.b64encode(value).decode()}
        else:
            return {"type": "text", "value": str(value)}


    def _post(self, body: dict) -> dict:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.pipeline_url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            raise ConnectionError(f"Turso HTTP {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Turso bağlantı hatası: {e.reason}")
        except Exception as e:
            raise ConnectionError(f"Turso istek hatası: {e}")


    def _parse_single_result(self, response: dict) -> TursoResult:
        results = response.get("results", [])
        if not results:
            return TursoResult()

        first = results[0]
        if first.get("type") == "error":
            error = first.get("error", {})
            raise RuntimeError(
                f"Turso SQL hatası: {error.get('message', 'Bilinmeyen hata')}"
            )

        result_data = first.get("response", {}).get("result", {})
        return TursoResult(result_data)

    def _parse_batch_results(self, response: dict) -> list:
        results = []
        for item in response.get("results", []):
            if item.get("type") == "error":
                error = item.get("error", {})
                raise RuntimeError(
                    f"Turso SQL hatası: {error.get('message', 'Bilinmeyen hata')}"
                )
            if item.get("type") == "ok":
                resp = item.get("response", {})
                if resp.get("type") == "execute":
                    results.append(TursoResult(resp.get("result", {})))
        return results
