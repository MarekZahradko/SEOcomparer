#!/usr/bin/env python3
"""SEO meta tag checker for Super pages ("toothpick" util).

Installed as the global `SEOinfo` command (see README). URLs may be given
without a scheme ("seznam.cz"); http:// is upgraded to https:// automatically.

Usage:
    SEOinfo example.super.site example.super.site/map-view

Standard library only. Runs on macOS and Linux with no setup.
"""

import argparse
import gzip
import html
import re
import sys
import urllib.error
import urllib.request
import zlib

TIMEOUT = 15
USER_AGENT = "super-seo-check/1.0 (+https://super.so)"

FIELDS = ["title", "description", "og:title", "og:description"]


class SeoCheckError(Exception):
    """Raised for expected failures we want to show as a clean message."""


def normalize_url(url):
    """Ensure the URL uses https. Bare host or http:// -> https://."""
    url = url.strip()
    if url.startswith("http://"):
        return "https://" + url[len("http://"):]
    if "://" not in url:
        return "https://" + url
    return url


def fetch(url):
    """Fetch a URL, returning the body as text. Raises SeoCheckError on failure."""
    url = normalize_url(url)
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            encoding = (resp.headers.get("Content-Encoding") or "").lower()
            if encoding == "gzip":
                raw = gzip.decompress(raw)
            elif encoding == "deflate":
                raw = zlib.decompress(raw)
            charset = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="replace")
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


def run_inspect(urls):
    for url in urls:
        try:
            print_block(url, parse_head(fetch(url)))
        except SeoCheckError as e:
            print(f"URL: {url}\n  Error: {e}\n", file=sys.stderr)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check SEO meta tags of Super pages.")
    parser.add_argument("urls", nargs="+", help="Page URLs to inspect")
    args = parser.parse_args(argv)

    try:
        return run_inspect(args.urls)
    except SeoCheckError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
