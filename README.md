# SEOcomparer

Small CLI tool ("toothpick") to check SEO meta tags of Super pages without opening DevTools.

Python 3, standard library only. Runs on macOS and Linux with no setup.

## Usage

Inspect one or more live pages:

```bash
python3 seo-check.py https://example.super.site/ https://example.super.site/map-view
```

Compare a path across prod vs staging (site-data API):

```bash
SUPER_API_SECRET=xxx python3 seo-check.py --compare /map-view --domain example.super.site
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | OK |
| 1 | `--compare`: description differs between prod and staging (usable in CI) |
| 2 | Environment/runtime error (missing `SUPER_API_SECRET`, page unreachable, …) |
