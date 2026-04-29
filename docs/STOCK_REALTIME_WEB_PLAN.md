# Stock Realtime Web Plan

## 1. Document Purpose

This document defines the project plan for a real-time stock query website intended for a professional stock-focused user.

The goal is not just to display prices, but to create a fast, high-signal decision support page for active market monitoring.

## 2. Product Goal

Build a browser-based stock monitoring workspace that allows a user to:

- query symbols quickly
- view real-time or near-real-time market data
- compare multiple symbols
- monitor custom watchlists
- inspect key indicators without switching between multiple websites

## 3. Target User

### Primary User

- A user working in stocks on a daily basis

### Typical Use Cases

- Checking intraday price movement
- Monitoring multiple watchlists
- Reviewing volume and turnover changes
- Watching leaders, laggards, and unusual moves
- Switching quickly between symbols and market segments

## 4. User Problems

The stock user usually faces these issues:

- Data is spread across multiple websites
- Pages are too slow or overloaded with noise
- Key symbols require repeated manual search
- Watchlists are not centralized
- Intraday tracking needs auto-refresh and alerting
- Market monitoring tools often optimize for casual investors, not active users

## 5. Product Positioning

This product should be a `focused real-time stock workspace`, not a generic financial portal.

That means:

- fast search
- fast refresh
- clear watchlists
- strong tabular and charting views
- low-noise interface

## 6. Core Product Modules

### 6.1 Symbol Search

Must support:

- search by ticker
- search by company name
- recent search history
- fast keyboard navigation

### 6.2 Quote Overview

Each symbol page should show:

- latest price
- change amount
- change percentage
- open
- high
- low
- previous close
- volume
- turnover
- market cap if available

### 6.3 Intraday Chart

Requirements:

- intraday line chart
- volume bars
- previous close reference line
- auto-refresh during trading hours

### 6.4 Watchlists

Users need multiple lists, for example:

- core holdings
- intraday focus
- breakouts
- sector watch
- news-driven names

Each watchlist should support:

- add/remove symbols
- drag reorder
- notes
- quick open in detail panel

### 6.5 Market Movers

High-value monitoring panels:

- top gainers
- top losers
- unusual volume
- turnover spikes
- sector leaders

### 6.6 Alerting

Alerts are a major value multiplier.

Examples:

- price above / below threshold
- percentage move threshold
- unusual volume
- intraday high breakout

## 7. Data Requirements

The product depends heavily on data quality.

Need to define:

- target market: US, A-shares, HK, or multi-market
- refresh frequency
- real-time vs delayed data
- permitted data sources
- rate limits and cost

## 8. Recommended Functional Scope

### MVP

- symbol search
- quote card
- intraday chart
- watchlist CRUD
- auto-refresh
- market movers table

### V1

- multi-watchlist workspace
- sortable tables
- alert rules
- historical daily chart
- recent search history

### V2

- sector heatmap
- custom dashboards
- user annotations
- event/news linkage
- strategy views

## 9. UX Principles

- `Fast first`: symbol lookup must be near-instant
- `Single-screen utility`: most actions should happen without page reload
- `Low-noise`: no portal-style clutter
- `Table + chart balance`: traders often scan tables first, charts second
- `Keyboard efficiency`: search and navigation should be fast

## 10. Suggested Interface Layout

### Left Sidebar

- watchlists
- saved screens
- market filters

### Top Search Bar

- symbol / company lookup
- quick jump

### Main Content

- quote overview
- intraday chart
- detail metrics

### Right Panel or Lower Panel

- alerts
- notes
- recent symbols
- market movers

## 11. Technical Plan

### Frontend

Recommended direction:

- modern SPA or server-driven reactive UI
- responsive but desktop-first
- charting library with live updates

### Backend

Backend responsibilities:

- quote proxy / aggregation
- watchlist storage
- alert rule evaluation
- caching and rate control

### Realtime Update Options

- polling for MVP
- websocket or SSE for later optimization

## 12. Data Source Layer

This should be abstracted early.

Need a provider layer that can later support:

- one market source
- multiple market providers
- failover or fallback sources

Do not hardcode provider-specific assumptions into the UI layer.

## 13. Security and Reliability

- API key management
- request throttling
- backend caching
- graceful degradation when provider is unavailable
- clear “realtime” vs “delayed” labels

## 14. Roadmap

### Phase 1: MVP

- search
- quote panel
- intraday chart
- one watchlist
- auto-refresh

### Phase 2: Daily Workflow

- multiple watchlists
- market movers
- notes
- sortable table views

### Phase 3: Action Layer

- alerts
- custom thresholds
- saved layouts

### Phase 4: Advanced Monitoring

- sector analysis
- anomaly screens
- cross-symbol comparison
- event-aware dashboards

## 15. Open Questions Before Implementation

These must be answered before development starts:

1. Which market is the priority?
2. Is true real-time required, or is delayed data acceptable initially?
3. Does the user need mobile support, or only desktop?
4. Are alerts in-page only, or also email / push / messaging?
5. Does the user need account login and cloud sync?

## 16. Recommended Immediate Next Tasks

1. Define the target market scope
2. Confirm acceptable data latency
3. Choose data provider strategy
4. Sketch the MVP page layout
5. Build a quote + watchlist prototype first

## 17. Final Recommendation

This stock project should be optimized for `speed, signal density, and repeat daily use`.

The best initial version is not a full financial platform.
It is a `fast real-time monitoring workspace` built around:

- search
- watchlists
- intraday price action
- alerts
- clean decision-oriented layout
