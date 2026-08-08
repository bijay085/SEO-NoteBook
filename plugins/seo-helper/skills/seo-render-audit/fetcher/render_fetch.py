"""OPTIONAL local renderer (Playwright).

The Claude-native default is to render the DOM with the browser MCP and pass the
saved HTML to `render_audit.py prep --rendered-file`. This module is only used as a
local fallback when Playwright happens to be installed and no rendered file was
supplied. The playwright import is therefore lazy : importing this module never
requires playwright to be present.
"""
import asyncio
import time
from config import RENDER_FETCH_TIMEOUT, RENDER_EXTRA_WAIT

GOOGLEBOT_UA = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; "
    "+http://www.google.com/bot.html)"
)


async def _fetch_rendered_async(url: str) -> dict:
    from playwright.async_api import async_playwright # lazy : optional dep

    result = {"html": "", "render_time_ms": 0,
              "console_errors": [], "error": None}
    t0 = time.time()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            page = await browser.new_page(user_agent=GOOGLEBOT_UA)
            errors = []
            page.on(
                "console",
                lambda m: errors.append(m.text) if m.type == "error" else None,
            )
            await page.goto(
                url,
                timeout=RENDER_FETCH_TIMEOUT,
                wait_until="networkidle",
            )
            # extra hold for late-firing JS (CMS calls, lazy loaders etc.)
            await page.wait_for_timeout(RENDER_EXTRA_WAIT)
            result["html"] = await page.content()
            result["console_errors"] = errors
        except Exception as e:
            result["error"] = str(e)
        finally:
            result["render_time_ms"] = int((time.time() - t0) * 1000)
            await browser.close()
    return result


def fetch_rendered(url: str) -> dict:
    """Sync wrapper. Returns a clean error dict if Playwright isn't installed,
    so the caller falls back to raw-only (the audit still runs, flagged)."""
    try:
        import playwright # noqa: F401
    except ImportError:
        return {
            "html": "", "render_time_ms": 0, "console_errors": [],
            "error": ("playwright not installed (optional local fallback) : "
                      "render via the browser / Playwright tool and pass --rendered-file"),
        }
    return asyncio.run(_fetch_rendered_async(url))
