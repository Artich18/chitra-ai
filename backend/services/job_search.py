"""Job search service using SerpAPI (Google Jobs engine).

This module performs a simple HTTP query to SerpAPI and normalizes
results into the application's `Job` shape.
"""
from __future__ import annotations

import os
import re
from typing import List

import requests


SERPAPI_URL = "https://serpapi.com/search.json"


def _extract_urls(text: str) -> List[str]:
    if not text:
        return []
    urls = re.findall(r"https?://[\w\-._~:/?#[\]@!$&'()*+,;=%]+", text)
    return list(dict.fromkeys(urls))


def search_jobs_serp(query: str, location: str | None = None, limit: int = 10) -> List[dict]:
    """Query SerpAPI (google_jobs) and return normalized job dicts.

    Requires environment variable `SERPAPI_KEY` to be set.
    """
    api_key = os.environ.get("SERPAPI_KEY", "")
    if not api_key:
        return []

    params = {"engine": "google_jobs", "q": query, "api_key": api_key}
    if location:
        params["location"] = location

    try:
        resp = requests.get(SERPAPI_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    results = []
    jobs = data.get("jobs_results") or data.get("jobs") or []
    for j in jobs[:limit]:
        title = j.get("title") or j.get("job_title") or j.get("position") or "Untitled Role"
        company = j.get("company_name") or j.get("company") or j.get("via") or "Unknown"
        location = j.get("location") or j.get("location_name") or j.get("area") or "Remote"
        description = j.get("description") or j.get("snippet") or j.get("summary") or ""
        posted = j.get("date_posted") or j.get("posted_date") or j.get("date")

        # Collect candidate apply links from common fields and the description
        apply_urls = []
        for k in ("apply_link", "link", "url", "job_posting_url", "destination_link"):
            v = j.get(k)
            if isinstance(v, str) and v:
                apply_urls.append(v)
        # Also scrape urls from description
        apply_urls.extend(_extract_urls(description))

        # Deduplicate while preserving order
        seen = set()
        apply_urls = [u for u in apply_urls if not (u in seen or seen.add(u))]

        results.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "posted": posted,
                "apply_urls": apply_urls,
                # fallback single apply_url for older UI
                "apply_url": apply_urls[0] if apply_urls else None,
            }
        )

    return results
