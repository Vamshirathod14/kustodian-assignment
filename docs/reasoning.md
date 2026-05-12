# Kustodian Assignment - Reasoning Document

## Tech Stack Decisions

### Backend: FastAPI + Python
- Chose FastAPI for built-in WebSocket support and async capabilities
- Async Python allows Playwright to run without blocking the event loop
- Automatic OpenAPI docs for easy testing

### Database: PostgreSQL
- ACID compliance for job state persistence
- JSONB support for storing extracted results
- Asyncpg driver for non-blocking database operations

### Browser Automation: Playwright
- More reliable than Selenium for modern web apps
- Built-in auto-waiting reduces flaky tests
- Excellent async API support

### Frontend: Next.js + TypeScript
- TypeScript for better developer experience
- Tailwind CSS for rapid UI development
- Built-in WebSocket support

## Job State Model

States: `pending` → `queued` → `running` → `completed` / `failed`

Why these states?
- `pending`: Job created, not yet processed
- `queued`: In memory queue, waiting for available worker
- `running`: Playwright actively browsing
- `completed/failed`: Terminal states with result or error

## Events Emitted (8+ distinct)

1. `browser.launching` - Playwright starting Chromium
2. `browser.launched` - Browser ready
3. `page.navigating` - Navigation started
4. `page.loaded` - Page loaded
5. `screenshot.captured` - Screenshot taken
6. `extracting.data` - Scraping content
7. `data.extracted` - Data parsed
8. `browser.closed` - Cleanup done
9. `job.completed/failed` - Final status

## Concurrency Handling
- Uses in-memory set to track active jobs
- Each job runs in its own asyncio task

## Trade-offs & Improvements

### Trade-offs made:
- In-memory job queue (jobs lost if backend crashes)
- No authentication (out of scope)
- Screenshots saved to /tmp (not persistent)

### What I would improve:
- Add Redis for persistent queue
- Implement job retry logic
- Add authentication
- Store screenshots in cloud storage
- Add pagination for log viewer