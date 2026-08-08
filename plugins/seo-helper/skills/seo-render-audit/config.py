# Deterministic config for the Claude-native render audit.
# No API keys, no model routing, no dotenv : Claude performs the reading /
# analysis / solution / writing passes itself, in-context.

# ── Fetch settings ────────────────────────────────────────────────────────────
RAW_FETCH_TIMEOUT = 15 # seconds (requests raw fetch)
RENDER_FETCH_TIMEOUT = 20000 # ms : optional local Playwright fallback only
RENDER_EXTRA_WAIT = 2000 # ms : extra hold after networkidle (Playwright only)

# ── AI / search crawler bots checked against robots.txt ───────────────────────
AI_BOTS = [
    "Googlebot",
    "GPTBot",
    "ClaudeBot",
    "PerplexityBot",
    "anthropic-ai",
    "Applebot-Extended",
]
