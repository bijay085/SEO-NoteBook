"""Optional Google Search Console connector.

Google client libraries are imported only inside the functions that need them.
If GSC_CREDENTIALS_PATH is unset or the optional packages are missing, callers
get a structured `{configured: False}` dict instead of an exception.
"""
from __future__ import annotations

import os
from pathlib import Path

_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
_HINT = (
    "Set GSC_CREDENTIALS_PATH to a Google service-account JSON file with "
    "Search Console access, install google-auth and google-api-python-client, "
    "then restart the MCP server."
)


def _credentials_path() -> str:
    return os.environ.get("GSC_CREDENTIALS_PATH", "").strip()


def is_configured() -> bool:
    path = _credentials_path()
    return bool(path and Path(path).expanduser().is_file())


def fetch_search_analytics(site_url, start_date, end_date, dimensions=None):
    """Wrap Search Console searchanalytics.query. Never raises for missing config."""
    raw = _credentials_path()
    if not raw:
        return {"configured": False, "hint": _HINT}
    path = str(Path(raw).expanduser())
    if not os.path.isfile(path):
        return {"configured": False, "hint": f"GSC_CREDENTIALS_PATH not found: {path}"}
    try:
        from google.oauth2 import service_account  # pyright: ignore[reportMissingImports]
        from googleapiclient.discovery import build  # pyright: ignore[reportMissingImports]
    except ImportError:
        return {
            "configured": False,
            "hint": "Install optional packages: google-auth and google-api-python-client",
        }
    dims = list(dimensions or [])
    try:
        creds = service_account.Credentials.from_service_account_file(path, scopes=_SCOPES)
        svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dims,
            "rowLimit": 25000,
        }
        data = svc.searchanalytics().query(siteUrl=site_url, body=body).execute()
        return {
            "configured": True,
            "ok": True,
            "site_url": site_url,
            "start_date": start_date,
            "end_date": end_date,
            "dimensions": dims,
            "rows": data.get("rows") or [],
        }
    except Exception as exc:  # noqa: BLE001
        return {"configured": True, "ok": False, "error": str(exc)}
