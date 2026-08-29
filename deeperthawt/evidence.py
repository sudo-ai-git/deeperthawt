#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
deeperthawt.evidence — deterministic token-cost intelligence (evidence layer).

MERGE (2026-08-29): wires token-analytics (agent-token-cost data product) into
the deeperthawt monorepo as the evidence endpoint. It reads real DeepSeek usage
data (the token-type daily aggregates) and emits a deterministic, publishable
JSON report of the token-cost profile of an agent workload — the measured
"why you save tokens with no-LLM verification" number behind the sales story.

Deterministic + no-LLM + no-network: pure CSV -> JSON reduction.
"""

import csv
import json
import os
from collections import defaultdict

# Location of the DeepSeek usage CSVs (kept out of the repo; path is env-tunable).
DATA_DIR = os.environ.get(
    "THAWT_EVIDENCE_DIR",
    "/mnt/c/Users/sudos/Downloads/usage_data_2026-08-22_2026-08-28",
)


def _load_rows():
    """Read all *.csv in DATA_DIR; bind each row to its file's TL date."""
    rows = []
    if not os.path.isdir(DATA_DIR):
        return rows
    for name in sorted(os.listdir(DATA_DIR)):
        if not name.endswith(".csv"):
            continue
        # embed the date the file covers for a stable series
        path = os.path.join(DATA_DIR, name)
        try:
            with open(path, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    rows.append({"file": name, **r})
        except OSError:
            continue
    return rows


def build_evidence_report() -> dict:
    """Reduce the usage CSVs into a deterministic token-cost / savings report."""
    rows = _load_rows()
    if not rows:
        return {
            "deterministic": True,
            "no_llm": True,
            "data_dir": DATA_DIR,
            "samples": 0,
            "note": "no usage CSVs found; set THAWT_EVIDENCE_DIR to the data dir",
        }
    by_type = defaultdict(int)
    days = set()
    samples = 0
    for r in rows:
        t = (r.get("type") or "").strip()
        try:
            amt = float(r.get("amount") or 0)
        except (TypeError, ValueError):
            amt = 0.0
        by_type[t] += amt
        samples += 1
        # day = the calendar date portion of start_time_iso (or date)
        dt = (r.get("start_time_iso") or r.get("date") or "").strip()[:10]
        if dt:
            days.add(dt)
    cache_hit = by_type.get("input_cache_hit_tokens", 0.0)
    cache_miss = by_type.get("input_cache_miss_tokens", 0.0)
    out_tok = by_type.get("output_tokens", 0.0)
    total_in = cache_hit + cache_miss
    n_days = len(days)
    return {
        "deterministic": True,
        "no_llm": True,
        "source": "DeepSeek usage CSV (token-type daily aggregates)",
        "data_dir": DATA_DIR,
        "days": n_days,
        "samples": samples,
        "input_tokens_total": round(total_in),
        "input_cache_hit_total": round(cache_hit),
        "input_cache_miss_total": round(cache_miss),
        "output_tokens_total": round(out_tok),
        "cache_hit_pct": (round(cache_hit / total_in * 100, 2) if total_in else None),
        "note": "measured agent workload; no-LLM verification removes the LLM token spend",
    }


if __name__ == "__main__":
    print(json.dumps(build_evidence_report(), indent=2))
