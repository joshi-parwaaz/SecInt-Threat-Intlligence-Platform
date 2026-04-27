"""
demo_seeder.py - Seeds the database with realistic IOC fixture data.

Runs automatically on startup when:
  - The 'iocs' collection is empty (fresh Atlas / Render deploy), OR
  - No OTX/VirusTotal API keys are configured (visitor demo mode).

This means the live demo always has data to show, even before the first
scheduled ingestion cycle completes.
"""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from database import get_collection

logger = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).parent.parent / "data" / "demo_iocs.json"
DEMO_MARKER = "__demo_seed__"


def _api_keys_present() -> bool:
    """Return True only if at least one live API key is configured."""
    return bool(
        os.getenv("OTX_API_KEY") or
        os.getenv("VIRUSTOTAL_API_KEY") or
        os.getenv("ABUSEIPDB_API_KEY")
    )


async def seed_demo_data(force: bool = False) -> int:
    """
    Seed the IOC collection from the fixture file if needed.

    Args:
        force: Skip all checks and always re-seed (useful for testing).

    Returns:
        Number of documents inserted (0 if seeding was skipped).
    """
    collection = get_collection("iocs")

    existing_count = await collection.count_documents({})

    if not force:
        # Skip if real data already exists
        if existing_count > 0 and _api_keys_present():
            logger.info(
                "⏭  Demo seeder: %d IOCs already in DB and API keys present — skipping.",
                existing_count,
            )
            return 0

        # Skip if demo data was previously seeded and keys are now present
        demo_marker = await collection.find_one({"_demo": DEMO_MARKER})
        if demo_marker and _api_keys_present():
            logger.info(
                "⏭  Demo seeder: demo data present and API keys configured — skipping.",
            )
            return 0

        if existing_count > 50 and not _api_keys_present():
            # Already seeded without keys — don't duplicate
            logger.info(
                "⏭  Demo seeder: collection already has %d docs — skipping.",
                existing_count,
            )
            return 0

    # Load fixture
    if not FIXTURE_PATH.exists():
        logger.error("❌ Demo fixture not found at %s", FIXTURE_PATH)
        return 0

    with open(FIXTURE_PATH, "r") as fh:
        fixtures: list[dict] = json.load(fh)

    if not fixtures:
        logger.warning("⚠️  Demo fixture file is empty.")
        return 0

    # Prepare documents
    now = datetime.now(timezone.utc)
    docs = []
    existing_values = set()

    # Collect existing ioc_values to avoid duplicates
    async for doc in collection.find({}, {"ioc_value": 1}):
        existing_values.add(doc.get("ioc_value"))

    for item in fixtures:
        if item.get("ioc_value") in existing_values:
            continue

        # Normalise datetime strings → datetime objects
        for ts_field in ("first_seen", "last_updated", "enrichment_timestamp"):
            raw = item.get(ts_field)
            if isinstance(raw, str):
                try:
                    item[ts_field] = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                except ValueError:
                    item[ts_field] = now

        # Tag as demo so we can identify / clean up later
        item["_demo"] = DEMO_MARKER
        item.setdefault("first_seen", now)
        item.setdefault("last_updated", now)
        docs.append(item)

    if not docs:
        logger.info("⏭  Demo seeder: all fixture IOCs already present — nothing to insert.")
        return 0

    result = await collection.insert_many(docs)
    inserted = len(result.inserted_ids)
    logger.info(
        "✅ Demo seeder: inserted %d IOCs from fixture (%s keys).",
        inserted,
        "no API" if not _api_keys_present() else "API keys present",
    )
    return inserted


async def clear_demo_data() -> int:
    """
    Remove all demo-seeded documents from the collection.
    Called automatically before the first real ingestion run
    so live data cleanly replaces fixture data.

    Returns:
        Number of documents deleted.
    """
    collection = get_collection("iocs")
    result = await collection.delete_many({"_demo": DEMO_MARKER})
    if result.deleted_count:
        logger.info("🧹 Demo seeder: removed %d demo IOCs.", result.deleted_count)
    return result.deleted_count
