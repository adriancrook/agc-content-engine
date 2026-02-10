# AGC v2 Web UI

## Overview
Beautiful, modern web interface for viewing and managing articles in the AGC v2 content engine pipeline.

## Features

### 📊 Dashboard
- Real-time stats (total articles, ready, enriching, writing)
- Filter articles by state
- Search articles by title
- Auto-refresh every 10 seconds
- Clean, dark-themed UI

### 📰 Article View
- **Enrichment Data:**
  - Citations with sources and URLs
  - Metrics from games
  - Testimonials
  - Integration guide for Writer Pass 2

- **Content Tabs:**
  - Draft (initial version)
  - Revised Draft (with enrichment integrated)
  - Final Content (after humanization)

- **Research Sources:**
  - View all research sources used
  - Direct links to original content

## Access

### Local Development
```
http://localhost:8000
```

### Railway Deployment
Your Railway deployment URL (replace with actual URL):
```
https://your-app.railway.app
```

## State Color Codes
- 🟢 **Ready** - Article complete
- 🟠 **Enriching** - Finding citations & metrics
- 🔵 **Writing** - Generating draft
- 🟣 **Researching** - Gathering sources
- 🌸 **Revising** - Integrating enrichment
- 🔴 **Failed** - Error occurred
- 🔵 **Fact Checking** - Verifying claims

## API Endpoints (for developers)

All API endpoints remain at `/articles`, `/status`, etc.

The root `/` now shows the web UI instead of JSON.

For API access, use:
- `GET /api` - API status
- `GET /articles` - List articles (JSON)
- `GET /articles/{id}` - Get article details (JSON)
- `GET /status` - Get system status (JSON)

## Deployment Notes

The web UI automatically works with your existing Railway deployment.
No additional configuration needed - just push and deploy!

Templates are in: `v2/templates/`
Static files in: `v2/static/` (currently empty, can add custom CSS/JS here)
