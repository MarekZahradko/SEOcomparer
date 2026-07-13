# SEOcomparer

Small CLI tool by Marek Zahradko to check SEO meta tags of Super pages without opening DevTools.

Python 3, standard library only. Runs on macOS and Linux with no setup.

## Install (global `SEOdescription` command)

Make the script runnable from anywhere as `SEOdescription`:

```bash
chmod +x seo-check.py
mkdir -p ~/.local/bin
ln -sf "$(pwd)/seo-check.py" ~/.local/bin/SEOdescription
```

If `~/.local/bin` is not on your `PATH`, add it (zsh):

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Now you can run it from any directory.

## Usage

Inspect one or more live pages:

```bash
SEOdescription https://example.super.site/
SEOdescription https://example.super.site/ https://example.super.site/map-view
```

Compare a path across prod vs staging (site-data API):

```bash
SUPER_API_SECRET=xxx SEOdescription --compare /map-view --domain example.super.site
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | OK |
| 1 | `--compare`: description differs between prod and staging (usable in CI) |
| 2 | Environment/runtime error (missing `SUPER_API_SECRET`, page unreachable, …) |
