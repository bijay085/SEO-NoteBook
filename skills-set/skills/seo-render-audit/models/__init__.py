from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SignalResult(BaseModel):
    signal_id:        str
    category:         str
    signal_name:      str
    raw_value:        Any = None
    rendered_value:   Any = None
    match:            bool = True
    severity:         str = "pass"
    effort:           Optional[str] = None
    impact:           Optional[str] = None
    gap_significance: str = "none"
    priority_rank:    int = 999
    severity_reason:  str = ""


class SolutionRecord(BaseModel):
    signal_id:        str
    url:              str
    category:         str
    severity:         str
    effort:           str
    impact:           str
    priority_rank:    int

    observed_in_raw:      str = ""
    observed_in_rendered: str = ""
    diagnosis:            str = ""
    fix:                  str = ""
    code_fix:             Optional[str] = None
    evidence_basis:       str = ""
    verify:               str = ""
    severity_reason:      str = ""

    prose:      str = ""
    code_block: Optional[str] = None


class FetchResult(BaseModel):
    url:            str
    status_code:    Optional[int] = None
    headers:        Dict[str, Any] = Field(default_factory=dict)
    raw_html:       str = ""
    rendered_html:  str = ""
    robots_txt:     Optional[str] = None
    llms_txt:       Optional[str] = None
    fetch_time_ms:  int = 0
    render_time_ms: int = 0
    redirect_chain: List[str] = Field(default_factory=list)
    console_errors: List[str] = Field(default_factory=list)
    final_url:      str = ""
    fetch_error:    Optional[str] = None
    render_error:   Optional[str] = None


class URLAuditResult(BaseModel):
    url:             str
    fetch:           FetchResult
    signals:         List[SignalResult]   = Field(default_factory=list)
    solutions:       List[SolutionRecord] = Field(default_factory=list)
    bot_access:      Dict[str, str]       = Field(default_factory=dict)
    llms_txt_status: str = "missing"
    scores:          Dict[str, int]       = Field(default_factory=dict)
    audit_status:    str = "pending"
    errors:          List[str]            = Field(default_factory=list)
    meta:            Dict[str, Any]       = Field(default_factory=dict)
