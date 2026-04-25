import httpx


class MemosError(Exception):
    pass


class MemosClient:
    def __init__(self, url: str, token: str) -> None:
        self.url = url.rstrip("/")
        self.token = token
        self._headers = {"Authorization": f"Bearer {token}"}

    def test_connection(self) -> bool:
        try:
            r = httpx.post(
                f"{self.url}/api/v1/auth/status",
                headers=self._headers,
                timeout=5,
            )
            return r.status_code == 200
        except Exception:
            return False

    def push(self, content: str) -> str:
        try:
            r = httpx.post(
                f"{self.url}/api/v1/memos",
                headers=self._headers,
                json={"content": content, "visibility": "PRIVATE"},
                timeout=10,
            )
        except Exception as e:
            raise MemosError(f"網路錯誤：{e}") from e
        if r.status_code != 200:
            raise MemosError(f"推送失敗 HTTP {r.status_code}")
        data = r.json()
        return str(data.get("uid") or data.get("id", ""))
