"""
scheduler.py - Background IOC refresh using APScheduler.

Runs every 6 hours when API keys are configured.
On the first run after startup it clears demo-seeded fixture data
so live threat intelligence replaces the seed corpus cleanly.
"""
import logging
import os
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# State
# ──────────────────────────────────────────────────────────────────────────────
scheduler: AsyncIOScheduler | None = None

refresh_state = {
    "running": False,
    "last_run": None,          # ISO timestamp of last completed run
    "last_result": None,       # dict with stats or error
    "next_run": None,          # ISO timestamp of next scheduled run
    "total_runs": 0,
}


# ──────────────────────────────────────────────────────────────────────────────
# Core refresh job
# ──────────────────────────────────────────────────────────────────────────────
async def _run_refresh() -> None:
    """
    Pull fresh IOCs from all configured threat feeds and persist them.
    On the very first run, demo-seeded data is cleared first.
    """
    global refresh_state

    if refresh_state["running"]:
        logger.warning("⚠️  Refresh already running — skipping this cycle.")
        return

    # Require at least OTX key for a meaningful refresh
    if not os.getenv("OTX_API_KEY") and not os.getenv("URLHAUS_API_KEY"):
        logger.info("ℹ️  No API keys configured — skipping scheduled refresh.")
        return

    refresh_state["running"] = True
    start = datetime.now(timezone.utc)
    logger.info("🔄 Scheduled IOC refresh starting at %s", start.isoformat())

    try:
        from services.demo_seeder import clear_demo_data
        from services.direct_ingest import DirectThreatIngestionService

        # First ever live run: remove fixture data
        if refresh_state["total_runs"] == 0:
            removed = await clear_demo_data()
            if removed:
                logger.info("🧹 Cleared %d demo IOCs before first live refresh.", removed)

        service = DirectThreatIngestionService()
        await service.ingest_otx_pulses(limit=20)
        await service.ingest_urlhaus_urls(limit=50)
        await service.ingest_urlhaus_payloads(limit=50)

        refresh_state["last_result"] = {
            "status": "success",
            "stats": service.stats,
            "duration_seconds": (datetime.now(timezone.utc) - start).total_seconds(),
        }
        refresh_state["total_runs"] += 1
        logger.info("✅ Scheduled refresh complete: %s", service.stats)

    except Exception as exc:
        logger.error("❌ Scheduled refresh failed: %s", exc, exc_info=True)
        refresh_state["last_result"] = {
            "status": "error",
            "error": str(exc),
        }
    finally:
        refresh_state["running"] = False
        refresh_state["last_run"] = datetime.now(timezone.utc).isoformat()
        _update_next_run()


def _update_next_run() -> None:
    """Cache the next scheduled run time for the status endpoint."""
    global refresh_state
    if scheduler:
        jobs = scheduler.get_jobs()
        if jobs:
            next_dt = jobs[0].next_run_time
            refresh_state["next_run"] = next_dt.isoformat() if next_dt else None


# ──────────────────────────────────────────────────────────────────────────────
# Lifecycle helpers called from main.py lifespan
# ──────────────────────────────────────────────────────────────────────────────
def start_scheduler(interval_hours: int = 6) -> None:
    """Start the APScheduler background scheduler."""
    global scheduler

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        _run_refresh,
        trigger=IntervalTrigger(hours=interval_hours),
        id="ioc_refresh",
        name="IOC Refresh",
        replace_existing=True,
        misfire_grace_time=300,   # 5-minute grace if the server was asleep
    )
    scheduler.start()
    _update_next_run()
    logger.info(
        "⏰ IOC refresh scheduler started — runs every %d hour(s). Next: %s",
        interval_hours,
        refresh_state["next_run"],
    )


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("⏹  IOC refresh scheduler stopped.")


def get_scheduler_status() -> dict:
    """Return a snapshot of scheduler state for the /health/scheduler endpoint."""
    return {
        **refresh_state,
        "scheduler_running": scheduler.running if scheduler else False,
    }
