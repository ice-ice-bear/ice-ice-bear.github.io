---
title: "trading-agent Dev Log #13 — Live Research Search, Agent Lifecycle Events"
description: "KOSPI200 live stock search, WebSocket event history hydration, agent lifecycle events, DART EPS field expansion, and Research page enrichment"
date: 2026-04-16
image: "/images/posts/2026-04-16-trading-agent-dev13/cover-en.jpg"
series: "trading-agent"
series_num: 13
last_commit: "84a5d11"
categories: ["tech-log"]
tags: ["trading-agent", "research", "kospi", "websocket", "dart"]
toc: true
math: false
---

## Overview

Major UX improvements to the Research page with live KOSPI200 stock search, plus a new agent lifecycle event system for real-time execution tracking. Also expanded DART API EPS field mapping to cover more industries. 3 sessions, roughly 8 hours total.

[Previous: trading-agent Dev Log #12](/posts/2026-04-15-trading-agent-dev12/)

<!--more-->

## Key Changes

### Research Live Search and Enriched Stock Detail

Added a live search dropdown to the Research page for KOSPI200 stocks. The backend performs local substring matching against the KOSPI200 list first, falling back to MCP only when no local results are found. This local-first approach keeps response times fast and reduces MCP call costs.

The stock detail view and price chart were also enriched — the stock detail component now displays richer information, and the chart visualization was improved.

### WebSocket Event History Hydration

Previously, only events arriving after the WebSocket connection was established would appear on the frontend. Refreshing the page or connecting late meant missing earlier agent events. Now the hook hydrates the full event history on mount before subscribing to the live stream. Users see the complete agent execution timeline regardless of when they open the page.

### Agent Lifecycle Events

Added three lifecycle events to the agent base class: `agent.started`, `agent.completed`, and `agent.failed`. These are emitted automatically when an agent begins execution, finishes successfully, or encounters a failure. Combined with the WebSocket hydration above, the frontend can now display real-time agent status.

### Reports View Fix

When selecting a report from the list, the view now fetches the full report instead of using the truncated payload from the list API. This fixes missing content in the detail view.

### DART EPS Field Expansion

Expanded the candidate field names used to extract EPS data from the DART API. Different industries use different field names for EPS in their financial statements — previously some industries returned no EPS data. The broader candidate list now covers more sectors.

### Miscellaneous

- Added logo and Android Chrome favicons for branding
- Cleaned up `.claudeignore` and `.gitignore` — excluded local tool state, screenshots, and mockup scratch files
- Added HarnessKit feature list and superpowers planning docs

## Commit Log

| Type | Description |
|------|-------------|
| docs | Add HarnessKit feature list, superpowers plans/specs, and progress log |
| chore | Add logo and android-chrome favicons |
| chore | Ignore local tool state, screenshots, and mockup scratch files |
| feat | Hydrate agent event history on mount before subscribing |
| fix | Fetch full report on selection instead of using list payload |
| feat | Live search dropdown, enriched stock detail and chart |
| feat | Local KOSPI200 substring search with MCP fallback |
| fix | Expand EPS field name candidates for broader industry coverage |
| feat | Emit agent started/completed/failed lifecycle events |

## Insights

- **Local-first search pattern**: Searching a local dataset before hitting an external API is effective for both latency and cost. For relatively static lists like KOSPI200 constituents, a local cache is sufficient.
- **Event hydration matters**: In real-time systems, restoring "pre-connection events" makes a significant UX difference. Fetching history before subscribing avoids both duplicates and gaps cleanly.
- **Standardized lifecycle events**: Emitting start/complete/fail from the agent base class gives you monitoring UI and logging for free. Individual agents no longer need to duplicate state management code.
- **Financial data field name diversity**: In Korean DART filings, the same metric (EPS) can appear under different field names depending on the industry. Relying on a single field name silently drops entire sectors — a candidate list approach is the pragmatic solution.
