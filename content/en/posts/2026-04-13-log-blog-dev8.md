---
title: "log-blog Dev Log #8 — URL Classifier Quality Bumps and Multilingual Taxonomy Path Fix"
description: log-blog dev log 8. Adds YouTube Shorts and Perplexity Computer detection to the URL classifier, and fixes a bug where taxonomy _index.md was written to the wrong path under multilingual mode.
date: 2026-04-13
image: "/images/posts/2026-04-13-log-blog-dev8/cover-en.jpg"
series: "log-blog"
series_num: 8
last_commit: "9f2f41f"
categories: ["dev-log"]
tags: ["log-blog", "python", "hugo", "i18n"]
toc: true
math: false
---

## Overview

Following [Previous Post: #7](/posts/2026-04-08-log-blog-dev7/), this is the 8th cycle. It covers two URL classifier quality fixes and one taxonomy-path bug found while running the multilingual blog. Three small fixes, but all three touch surfaces a user notices instantly — classification accuracy and build success.

<!--more-->

---

## URL Classifier — Perplexity Computer + Billing Page Filter

### Background

Perplexity's newly launched Computer Agent URLs were appearing in extracted history, but the classifier was dropping them into generic `web_page`. At the same time, RunPod billing/account pages were leaking personal account data while still being classified as a "tech URL."

### Implementation

Two changes to `url_classifier.py`'s dispatch table:
- Added Perplexity Computer agent pattern → `ai_chat_perplexity`
- Moved explicit billing patterns (`/billing`, `/account`) into the default-filter set

### Result

Billing pages no longer surface in history extracts, and Perplexity Computer results now classify correctly into the AI chat group.

---

## URL Classifier — YouTube Shorts and GitHub Accuracy

### Background

The classifier didn't detect YouTube Shorts (`youtube.com/shorts/...`) and dropped them into generic web_page. Separately, GitHub URLs containing `/blob/`, `/tree/`, or `/commit/` were misclassified as `github_repo`, causing the fetcher to try and pull a README that wasn't there.

### Implementation

```python
# Add YouTube Shorts pattern
re.compile(r"youtube\.com/shorts/"): UrlType.YOUTUBE,
# Strengthen GitHub repo pattern — split blob/tree/commit into github_other
```

### Result

YouTube Shorts are now valid transcript fetch targets, and GitHub `/blob/` URLs are split into a separate category (`github_other`), eliminating fetcher failures.

---

## Multilingual Taxonomy Path Bug

### Background

After the blog moved to bilingual (Korean/English), creating a new tag wrote `_index.md` to `content/tags/{tag}/_index.md`. But in multilingual mode, Hugo expects `content/{lang}/tags/{tag}/_index.md`. Result: every new tag 404'd on the English homepage.

### Implementation

```mermaid
graph LR
    A[Old: content/tags/{tag}/] --> B[Hugo i18n &lt;br/&gt; cannot resolve]
    A --> C[New: content/{lang}/tags/{tag}/]
    C --> D[Routes correctly]
```

The taxonomy `_index` writer in `image_handler.py` now accepts the `--language` flag and writes under `language_content_dirs[lang]`. When the publish command runs both languages, both `_index` files are created.

### Result

The previously-broken tag index on the English blog now works, confirmed live after a cache bust.

---

## Commit Log

| Message | Files |
|---------|-------|
| fix: classify Perplexity Computer agent URLs and filter billing pages | url_classifier.py |
| fix: improve URL classifier quality — YouTube Shorts, noise filtering, GitHub accuracy | url_classifier.py |
| fix: write taxonomy _index.md under language content root | image_handler.py |

---

## Insights

All three fixes were of the form "what assumption did we wrongly model about another component (Chrome history DB, Hugo i18n)?" The URL classifier is essentially a set of assumptions about external site URL schemas — when a new pattern like Perplexity Computer ships, those assumptions go stale immediately. The multilingual taxonomy bug was more interesting: Hugo's multilingual mode keeps the *default* content directory in place, but taxonomy indexes have to move under the language root. That asymmetry is exactly the kind of thing that breaks first at the single-language → multilingual transition.
