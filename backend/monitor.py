import asyncio
import datetime
import logging
import time
from typing import Dict

import httpx

from database import SessionLocal
from models import Incident, MonitoredURL, PingResult, URLStatus
from notifications import send_webhook

logger = logging.getLogger("uptime_monitor.scheduler")

FAILURE_THRESHOLD = 2  # consecutive failed pings before we call a URL DOWN (avoids flapping on one blip)
DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_CONCURRENT_PINGS = 20  # cap outbound requests in flight across all URLs

_ping_semaphore = asyncio.Semaphore(MAX_CONCURRENT_PINGS)


class MonitorManager:
    """
    Owns one asyncio task per monitored URL, so each URL runs on its own
    check_interval_seconds instead of everything being forced onto one global tick.
    """

    def __init__(self):
        self._tasks: Dict[int, asyncio.Task] = {}

    def start_all(self) -> None:
        db = SessionLocal()
        try:
            for url in db.query(MonitoredURL).all():
                self.start(url.id)
        finally:
            db.close()

    def start(self, url_id: int) -> None:
        if url_id in self._tasks:
            return
        self._tasks[url_id] = asyncio.create_task(self._loop(url_id))

    def stop(self, url_id: int) -> None:
        task = self._tasks.pop(url_id, None)
        if task:
            task.cancel()

    def stop_all(self) -> None:
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()

    async def _loop(self, url_id: int) -> None:
        while True:
            db = SessionLocal()
            interval = 60
            try:
                url = db.query(MonitoredURL).filter(MonitoredURL.id == url_id).first()
                if url is None:
                    return  # URL got deleted -> stop rescheduling this task
                interval = url.check_interval_seconds
                await self._ping_and_record(db, url)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # one bad cycle should never kill the loop
                logger.exception(f"monitor loop error for url_id={url_id}: {exc}")
            finally:
                db.close()
            await asyncio.sleep(interval)

    async def _ping_and_record(self, db, url: MonitoredURL) -> None:
        start = time.perf_counter()
        status_code = None
        async with _ping_semaphore:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url.url, timeout=DEFAULT_TIMEOUT_SECONDS, follow_redirects=True)
                    status_code = resp.status_code
            except httpx.RequestError:
                status_code = None  # DNS failure, timeout, connection refused, etc.
        elapsed_ms = (time.perf_counter() - start) * 1000

        expected = url.expected_status_code
        is_success = status_code is not None and (
            status_code == expected if expected is not None else status_code < 400
        )

        db.add(PingResult(
            url_id=url.id,
            status_code=status_code,
            response_time_ms=elapsed_ms,
            is_success=is_success,
        ))

        await self._handle_status_transition(db, url, is_success)
        db.commit()

    async def _handle_status_transition(self, db, url: MonitoredURL, is_success: bool) -> None:
        if is_success:
            was_down = url.current_status == URLStatus.DOWN
            url.consecutive_failures = 0
            url.current_status = URLStatus.UP

            if was_down:
                open_incident = (
                    db.query(Incident)
                    .filter(Incident.url_id == url.id, Incident.ended_at.is_(None))
                    .first()
                )
                if open_incident:
                    open_incident.ended_at = datetime.datetime.utcnow()
                await send_webhook(url.webhook_url, {
                    "event": "url_recovered",
                    "url": url.url,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                })
        else:
            url.consecutive_failures += 1
            if url.consecutive_failures >= FAILURE_THRESHOLD and url.current_status != URLStatus.DOWN:
                url.current_status = URLStatus.DOWN
                db.add(Incident(url_id=url.id, started_at=datetime.datetime.utcnow()))
                await send_webhook(url.webhook_url, {
                    "event": "url_down",
                    "url": url.url,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                })


manager = MonitorManager()
