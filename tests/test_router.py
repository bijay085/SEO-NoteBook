"""Situation → notebook section routing tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from seo_router_server import route_situation  # noqa: E402


def _sid(situation: str) -> str:
    return route_situation(situation)["section_id"]


def test_traffic_drop_routes_to_decline_diagnosis():
    assert _sid("organic traffic dropped on Shopify") == "decline-diagnosis"


def test_ranking_down_routes_to_decline_diagnosis():
    assert _sid("ranking down after the core update") == "decline-diagnosis"


def test_lost_traffic_after_migration_routes_to_decline():
    assert _sid("lost traffic after migration") == "decline-diagnosis"


def test_sandbox_phrase_routes_to_decline_diagnosis():
    assert _sid("indexed but not ranking, not graduating") == "decline-diagnosis"


def test_topical_map_phrase():
    assert _sid("build a topical map for this niche") == "topical-map"


def test_content_cluster_phrase():
    assert _sid("content cluster and keyword map") == "topical-map"


def test_render_js_routes_to_technical_seo():
    assert _sid("javascript rendered DOM vs raw html") == "technical-seo"


def test_robots_blocked_routes_to_technical_seo():
    assert _sid("robots.txt crawl blocked googlebot") == "technical-seo"


def test_canonical_routes_to_technical_seo():
    assert _sid("google-selected canonical mismatch") == "technical-seo"


def test_log_file_routes_to_technical_seo():
    assert _sid("log file crawl budget waste") == "technical-seo"


def test_backlink_routes_to_technical_seo():
    assert _sid("toxic link and backlink profile") == "technical-seo"


def test_location_page_overlap_prefers_local_gbp():
    """'location page' is in both local-gbp and service-location-pages; score-tie breaks on id."""
    result = route_situation("location page")
    assert result["section_id"] == "local-gbp"
    assert result["confidence"] == "low"
    assert result["alternate_section_id"] == "service-location-pages"


def test_location_page_local_seo_without_overlap():
    assert _sid("gbp google business profile") == "local-gbp"


def test_location_page_city_doorway_rule():
    assert _sid("city page doorway same content") == "service-location-pages"


def test_eeat_authorship_phrase():
    assert _sid("eeat authorship author missing") == "content-eeat"


def test_affiliate_review_routes_to_content_eeat():
    assert _sid("affiliate review site disclosure") == "content-eeat"


def test_new_site_routes_to_domain_understanding():
    assert _sid("new site new domain what is this business") == "domain-understanding"


def test_money_page_cro_phrase():
    assert _sid("money page conversion cro") == "money-pages"


def test_schema_routes_to_structured_data():
    assert _sid("schema structured data rich result") == "structured-data"


def test_weekly_report_phrase():
    assert _sid("weekly report for the client") == "weekly-reporting"


def test_nonsense_falls_back_to_decision_router():
    result = route_situation("asdf qwerty zxcv banana")
    assert result["section_id"] == "decision-router"
    assert result["mode"] == "simple-or-clarify"


def test_high_confidence_when_one_route_leads():
    result = route_situation("topical map")
    assert result["section_id"] == "topical-map"
    assert result["confidence"] == "high"
    assert "alternate_section_id" not in result
