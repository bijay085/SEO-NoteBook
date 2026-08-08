import time
import requests
from config import RAW_FETCH_TIMEOUT
from models import FetchResult

GOOGLEBOT_UA = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; "
    "+http://www.google.com/bot.html)"
)

HEADERS = {
    "User-Agent": GOOGLEBOT_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    # Do NOT send Accept-Encoding : let requests handle decompression
    # automatically via its default behaviour. Explicitly requesting
    # gzip can cause some servers to return compressed bytes that
    # requests fails to decode if Content-Encoding header is absent.
}


def fetch_raw(url: str) -> FetchResult:
    t0 = time.time()
    result = FetchResult(url=url)
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=RAW_FETCH_TIMEOUT,
            allow_redirects=True,
        )
        # Force UTF-8 if charset is missing : prevents garbled text
        if r.encoding is None or r.encoding.lower() in ("utf-8", ""):
            r.encoding = r.apparent_encoding or "utf-8"

        result.status_code = r.status_code
        result.headers = dict(r.headers)
        result.raw_html = r.text # full : never sliced
        result.fetch_time_ms = int((time.time() - t0) * 1000)
        result.final_url = str(r.url)
        result.redirect_chain = [str(h.url) for h in r.history]
    except requests.RequestException as e:
        result.fetch_error = str(e)
        result.fetch_time_ms = int((time.time() - t0) * 1000)
    return result
