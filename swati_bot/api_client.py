"""Client for Manas's REST API (Swati)."""
import requests


class ApiError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class ApiClient:
    def __init__(self, base_url, session=requests, timeout=10):
        self.base, self.s, self.timeout = base_url.rstrip("/"), session, timeout

    def _get(self, path, **params):
        try:
            r = self.s.get(self.base + path, params=params, timeout=self.timeout)
        except Exception as e:                       # network problems, DNS, timeouts
            raise ApiError(str(e)) from e
        if r.status_code >= 500:
            raise ApiError(f"server error {r.status_code}", r.status_code)
        try:
            body = r.json()
        except ValueError as e:
            raise ApiError("bad json") from e
        if r.status_code >= 400:
            raise ApiError(body.get("error", "error"), r.status_code)
        return body

    def nearest(self, lat, lon):
        return self._get("/api/nearest", lat=lat, lon=lon)

    def risk(self, node_id):
        return self._get(f"/api/nodes/{node_id}/risk")

    def crop_advice(self, lat, lon, irrigated=False):
        return self._get("/api/crop-advice", lat=lat, lon=lon, irrigated="1" if irrigated else "0")

    def alerts(self, since_id=0):
        return self._get("/api/alerts", since_id=since_id)["alerts"]
