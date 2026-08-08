#!/usr/bin/env python3
"""Audit a lead-capture form and generate a QA test plan.

Usage:
    python form_audit.py <form_page.html> <out_dir> [form_url]

Picks the primary lead form on the page (most name/email/phone/message fields,
never a search box), extracts its fields, runs static checks, and emits a
parameterised ~20-case manual QA test plan. Writes ``<out_dir>/form_audit.json``.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from common import load_page, soup_of, write_json

_ROLE = [
    ("email", re.compile(r"email", re.I)),
    ("phone", re.compile(r"\b(tel|phone|mobile|number)\b", re.I)),
    ("message", re.compile(r"\b(message|help|comment|detail|issue|need|inquir)\b", re.I)),
    ("name", re.compile(r"\b(name|company|business|full[-_ ]?name)\b", re.I)),
]


def _label_for(field, soup) -> str:
    fid = field.get("id")
    if fid:
        lab = soup.find("label", attrs={"for": fid})
        if lab and lab.get_text(strip=True):
            return lab.get_text(" ", strip=True)
    for attr in ("placeholder", "aria-label", "title"):
        if field.get(attr):
            return field.get(attr).strip()
    parent_lab = field.find_parent("label")
    if parent_lab:
        return parent_lab.get_text(" ", strip=True)
    return field.get("name", "") or field.get("type", "")


def _role_of(field, label) -> str:
    hay = f"{field.get('type','')} {field.get('name','')} {label}"
    if field.name == "textarea":
        return "message"
    if (field.get("type") or "").lower() == "email":
        return "email"
    if (field.get("type") or "").lower() == "tel":
        return "phone"
    for role, rx in _ROLE:
        if rx.search(hay):
            return role
    return "other"


def _pick_form(soup):
    """Return the most form-like <form>, or None."""
    best, best_score = None, -1
    for form in soup.find_all("form"):
        fields = form.select("input, textarea, select")
        real = [f for f in fields if (f.get("type") or "text").lower()
                not in ("hidden", "submit", "button", "search", "image")]
        if any((f.get("type") or "").lower() == "search" for f in fields):
            continue
        score = len(real) + 2 * bool(form.select('textarea')) + \
            2 * bool(form.select('input[type="email"]'))
        if score > best_score:
            best, best_score = form, score
    return best


def build(page_path, form_url=None):
    url, html = load_page(page_path)
    form_url = form_url or url
    soup = soup_of(html)
    form = _pick_form(soup)
    if form is None:
        return {"form_url": form_url, "found": False, "field_count": 0,
                "fields": [], "static_findings": 0, "test_plan": []}
    fields, static = [], 0
    for f in form.select("input, textarea, select"):
        ftype = (f.get("type") or ("textarea" if f.name == "textarea" else "text")).lower()
        if ftype in ("hidden", "submit", "button", "image"):
            continue
        label = _label_for(f, soup)
        role = _role_of(f, label)
        required = f.has_attr("required") or f.get("aria-required") == "true"
        maxlength = f.get("maxlength", "")
        if not maxlength and ftype in ("text", "email", "tel", "textarea"):
            static += 1                      # unbounded input length
        if role in ("name", "email", "phone", "message") and not required:
            static += 1                      # expected-required field not marked
        fields.append({
            "tag": f.name, "name": f.get("name", ""), "type": ftype,
            "label": label, "required": bool(required),
            "maxlength": maxlength, "pattern": f.get("pattern", ""), "role": role,
        })
    roles = {fd["role"] for fd in fields}
    return {"form_url": form_url, "found": True, "field_count": len(fields),
            "fields": fields, "static_findings": static,
            "test_plan": _test_plan(roles)}


def _tc(i, cat, scenario, target, expected):
    return {"id": f"TC{i:02d}", "category": cat, "scenario": scenario,
            "target_field": target, "expected": expected,
            "actual": "", "verdict": "", "severity": "", "fix": ""}


def _test_plan(roles) -> list:
    tcs, i = [], 1
    def add(*a):
        nonlocal i
        tcs.append(_tc(i, *a)); i += 1
    add("Happy Path", "Valid full submission", "form", "Submits and reaches the thank-you page.")
    add("Happy Path", "Valid - minimal required fields only", "form", "Submits, or validates if a blank field is actually required.")
    add("Required Fields", "Empty form - submit nothing", "form", "Inline validation errors; does not submit.")
    if "name" in roles:
        add("Required Fields", "Missing Name", "name", "Validation error; does not submit.")
    if "email" in roles:
        add("Required Fields", "Missing Email", "email", "Validation error; does not submit.")
        add("Email Validation", "Email - missing @", "email", "Validation error.")
        add("Email Validation", "Email - missing domain extension", "email", "Validation error.")
        add("Email Validation", "Email - double @@ signs", "email", "Validation error.")
        add("Email Validation", "Email - spaces inside", "email", "Validation error.")
    if "phone" in roles:
        add("Phone Validation", "Phone - alphabetic characters", "phone", "Validation error, or accepted then flagged.")
        add("Phone Validation", "Phone - only 2 digits", "phone", "Validation error - too short.")
        add("Phone Validation", "Phone - international format +44 / +1 (xxx)", "phone", "Accepted - valid international numbers must not be rejected.")
        add("Phone Validation", "Phone - special characters only", "phone", "Validation error.")
    add("Security", "XSS string in a text field", "name", "Sanitised / escaped - never executed.")
    add("Security", "SQL-injection string in a text field", "name", "Stored safely as text (parameterised queries).")
    if "message" in roles:
        add("Security", "XSS string in the Message field", "message", "Sanitised / escaped.")
    add("Boundary", "Extremely long name (500 chars)", "name", "Truncated or rejected - not stored unbounded.")
    if "message" in roles:
        add("Boundary", "Extremely long message (5000 chars)", "message", "Accepted within a cap, or rejected gracefully.")
    add("Boundary", "Whitespace-only values", "form", "Validation error - whitespace is not a value.")
    add("Special Chars", "Non-ASCII name (Arabic / accents)", "name", "Accepted - international names must work.")
    return tcs


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    page_path, out_dir = argv[0], argv[1]
    form_url = argv[2] if len(argv) > 2 else None
    data = build(page_path, form_url)
    write_json(Path(out_dir) / "form_audit.json", data)
    print(f"form_audit: found={data['found']} fields={data['field_count']} "
          f"static_findings={data['static_findings']} tests={len(data['test_plan'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
