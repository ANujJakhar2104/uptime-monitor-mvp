# AI Collaboration Log

## 1. The AI Tech Stack
*   **Backend Logic & Debugging:** Google Gemini (FastAPI architecture, asynchronous background worker orchestration, and SQLite database mapping).
*   **Frontend Generation:** Claude Opus (UI design and Tailwind CSS layout structuring).
*   **Environment & Execution:** Local terminal execution, Uvicorn, and Docker.

## 2. The Prompts
*   *Backend Initialization:* "Write a FastAPI application that allows me to submit a URL and an interval, and saves it to a SQLite database using SQLAlchemy."
*   *Background Worker:* "Write an asynchronous background task in Python that loops through the URLs in the database and pings them using httpx."
*   *Docker Orchestration:* "Write a docker-compose.yml that orchestrates my two containers. The backend (build context: ./backend) should expose port 8000. The frontend (build context: ./frontend) should expose port 80. Ensure they are on the same bridge network."

## 3. Course Corrections & Debugging
*   **Timeout Exception & Crash Prevention:** The background task crashed when a URL timed out or failed to load. I prompted the AI to wrap the request in a `try/except` block with a strict 5.0-second timeout, ensuring that network failures record a `DOWN` status in the database instead of halting the entire monitoring loop.

*   **Sync vs. Async Lifespan Error:** When initializing the background loop in FastAPI's lifespan context, the server crashed with `TypeError: a coroutine was expected, got None`. I prompted the AI to correct the event loop integration, resolving the issue by properly defining `start_all()` as an `async def` coroutine.

*   **WAF Blocking (403 Forbidden):** Commercial sites were returning false `DOWN` statuses because their firewalls blocked the default Python `httpx` library. I prompted the AI to inject a standard Chrome `User-Agent` header into the async client to bypass the firewall and accurately reflect the site's true uptime.