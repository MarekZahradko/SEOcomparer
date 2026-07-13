# SEOcomparer

This is a small tool that shows the SEO meta tags of a web page. It reads the
title, description and og tags so you don't have to open DevTools. It only uses
Python 3 and the standard library, so there is nothing to install. You can run
it on one URL or many URLs at the same time.

## Install

```bash
chmod +x seo-check.py
mkdir -p ~/.local/bin
ln -sf "$(pwd)/seo-check.py" ~/.local/bin/SEOinfo
```

If `~/.local/bin` is not on your PATH, add it:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Example

```
$ SEOinfo super.so
URL: super.so
  title:          Super — Create Custom Websites with Notion
  description:    Create a custom website in less than a minute with instant page loads, SEO optimization, and customized theming.
  og:title:       Super — Create Custom Websites with Notion
  og:description: Create a custom website in less than a minute with instant page loads, SEO optimization, and customized theming.
```
