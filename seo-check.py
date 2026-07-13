#!/usr/bin/env python3
"""SEO meta tag checker for Super pages ("toothpick" util).

Usage:
    # Inspect one or more live pages (HTML):
    python3 seo-check.py https://example.super.site/ https://example.super.site/map-view

    # Compare a path across prod vs staging site-data API:
    SUPER_API_SECRET=xxx python3 seo-check.py --compare /map-view --domain example.super.site

Exit codes:
    0  OK
    1  --compare: description differs between prod and staging (usable in CI)
    2  environment/runtime error (missing SUPER_API_SECRET, page unreachable, ...)

Standard library only. Runs on macOS and Linux with no setup.
"""

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 15
USER_AGENT = "super-seo-check/1.0 (+https://super.so)"
STAGING_SITE_DATA = "https://staging.api-v2.super.so/site-data/{domain}?page={path}&noCache=true&secret={secret}"

FIELDS = ["title", "description", "og:title", "og:description"]


class SeoCheckError(Exception):
    """Raised for expected failures we want to show as a clean message."""


def fetch(url):
    """Fetch a URL, returning the body as text. Raises SeoCheckError on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as e:
        raise SeoCheckError(f"HTTP {e.code} {e.reason} for {url}")
    except urllib.error.URLError as e:
        raise SeoCheckError(f"Could not reach {url}: {e.reason}")
    except TimeoutError:
        raise SeoCheckError(f"Timed out after {TIMEOUT}s for {url}")


def _isolate_head(document):
    match = re.search(r"<head[^>]*>(.*?)</head>", document, re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else document


def _attrs(tag):
    """Parse a tag's attributes into a dict, order-independent."""
    return {
        name.lower(): html.unescape(value)
        for name, value in re.findall(
            r"""([a-zA-Z:_-]+)\s*=\s*["']([^"']*)["']""", tag
        )
    }


def parse_head(document):
    """Extract SEO fields from HTML. Missing tag -> None."""
    head = _isolate_head(document)
    result = {field: None for field in FIELDS}

    title = re.search(r"<title[^>]*>(.*?)</title>", head, re.IGNORECASE | re.DOTALL)
    if title:
        result["title"] = html.unescape(title.group(1).strip())

    for tag in re.findall(r"<meta\b[^>]*>", head, re.IGNORECASE):
        attrs = _attrs(tag)
        key = attrs.get("name") or attrs.get("property")
        if key in ("description", "og:title", "og:description"):
            result[key] = attrs.get("content", "")

    return result


def fetch_staging(domain, path, secret):
    """Read SEO fields from the staging site-data API (JSON props.head)."""
    url = STAGING_SITE_DATA.format(
        domain=domain, path=urllib.parse.quote(path, safe=""), secret=secret
    )
    body = fetch(url)
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise SeoCheckError(f"Staging site-data did not return JSON for {domain}{path}")

    head = (data.get("props") or {}).get("head") or {}
    return {field: head.get(field) for field in FIELDS}


def render_value(value):
    if value is None:
        return "(missing)"
    if value == "":
        return "(empty)"
    return value


def print_block(url, fields):
    print(f"URL: {url}")
    width = max(len(f) for f in FIELDS) + 1
    for field in FIELDS:
        print(f"  {field + ':':<{width}} {render_value(fields[field])}")
    print()


def print_comparison(path, prod, staging):
    label_w = max(len(f) for f in FIELDS)
    col_w = 40
    header = f"  {'field':<{label_w}}  {'prod':<{col_w}}  staging"
    print(f"Compare: {path}\n")
    print(header)
    print("  " + "-" * (label_w + col_w + len(header) // 4))
    for field in FIELDS:
        p, s = prod[field], staging[field]
        flag = " ⚠️" if p != s else ""
        pv = render_value(p)
        sv = render_value(s)
        print(f"  {field:<{label_w}}  {pv[:col_w]:<{col_w}}  {sv}{flag}")
    print()


def run_compare(path, domain):
    if not path.startswith("/"):
        path = "/" + path
    secret = os.environ.get("SUPER_API_SECRET")
    if not secret:
        print("Error: SUPER_API_SECRET is not set (required for staging site-data).", file=sys.stderr)
        return 2

    prod = parse_head(fetch(f"https://{domain}{path}"))
    staging = fetch_staging(domain, path, secret)
    print_comparison(path, prod, staging)

    if prod["description"] != staging["description"]:
        print("Description differs between prod and staging.", file=sys.stderr)
        return 1
    return 0


def run_inspect(urls):
    for url in urls:
        try:
            print_block(url, parse_head(fetch(url)))
        except SeoCheckError as e:
            print(f"URL: {url}\n  Error: {e}\n", file=sys.stderr)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check SEO meta tags of Super pages.")
    parser.add_argument("urls", nargs="*", help="Page URLs to inspect")
    parser.add_argument("--compare", metavar="PATH", help="Compare a path (e.g. /map-view) across prod vs staging")
    parser.add_argument("--domain", help="Domain to use with --compare (e.g. example.super.site)")
    args = parser.parse_args(argv)

    try:
        if args.compare:
            if not args.domain:
                parser.error("--compare requires --domain")
            return run_compare(args.compare, args.domain)
        if not args.urls:
            parser.error("provide at least one URL, or use --compare with --domain")
        return run_inspect(args.urls)
    except SeoCheckError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
