import requests
from requests.adapters import HTTPAdapter
from typing import Optional, List, Dict
from urllib.parse import urlparse


def _domain_root(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _session() -> requests.Session:
    """Return a session that works on macOS regardless of LibreSSL vs OpenSSL."""
    s = requests.Session()
    try:
        import ssl
        from urllib3.util.ssl_ import create_urllib3_context

        class _TLSAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                ctx = create_urllib3_context()
                ctx.minimum_version = ssl.TLSVersion.TLSv1_2
                kwargs["ssl_context"] = ctx
                super().init_poolmanager(*args, **kwargs)

        s.mount("https://", _TLSAdapter())
    except Exception:
        pass
    return s


def fetch_robots(url: str) -> Optional[str]:
    root = _domain_root(url)
    try:
        r = _session().get(f"{root}/robots.txt", timeout=10)
        return r.text if r.status_code == 200 else None
    except Exception:
        return None


def fetch_llms_txt(url: str) -> Optional[str]:
    root = _domain_root(url)
    try:
        r = _session().get(f"{root}/llms.txt", timeout=10)
        return r.text if r.status_code == 200 else None
    except Exception:
        return None


def parse_bot_access(robots_txt: Optional[str], url_path: str,
                     bots: List[str]) -> Dict[str, str]:
    """
    Returns per-bot status for the given path.
    Status: "allow" | "block" | "not_mentioned"
    """
    if not robots_txt:
        return {b: "not_mentioned" for b in bots}

    results = {}
    lines = robots_txt.splitlines()

    for bot in bots:
        results[bot] = _check_bot(lines, bot, url_path)
    return results


def _check_bot(lines: List[str], bot: str, path: str) -> str:
    """
    Parse robots.txt lines for a specific user-agent.
    Handles wildcards and both Allow/Disallow directives.
    Last matching rule wins per Google's implementation.
    """
    in_block = False
    status = "not_mentioned"
    specificity = -1 # track rule specificity (longer = more specific)

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.lower().startswith("user-agent:"):
            ua = line.split(":", 1)[1].strip()
            in_block = (
                ua.lower() == bot.lower()
                or ua == "*"
            )
            continue

        if not in_block:
            continue

        if line.lower().startswith("disallow:"):
            rule = line.split(":", 1)[1].strip()
            if _path_matches(path, rule) and len(rule) > specificity:
                specificity = len(rule)
                status = "block"

        elif line.lower().startswith("allow:"):
            rule = line.split(":", 1)[1].strip()
            if _path_matches(path, rule) and len(rule) > specificity:
                specificity = len(rule)
                status = "allow"

    return status if status != "not_mentioned" else "allow"


def _path_matches(path: str, rule: str) -> bool:
    if not rule or rule == "/":
        return True
    return path.startswith(rule.rstrip("*"))
