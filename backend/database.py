"""
database.py - MongoDB connection, indexes, and collection helpers.

Performance strategy:
  - All indexes created once on startup via ensure_indexes()
  - Compound indexes cover the most common query patterns (type+severity, source+severity)
  - Text index on ioc_value + description + malware_family powers the search endpoint
  - Motor connection pool sized for Render free tier (single instance, low concurrency)
"""
import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure, OperationFailure

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/secint")
DB_NAME = "secint"

client: AsyncIOMotorClient = None
db = None


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------
# Each tuple is (index_spec, kwargs) passed to create_index.
# Keep this list in sync with the query patterns in routers/iocs.py.
_IOC_INDEXES = [
    # Primary sort — dashboard default sort order
    ([("severity_score", DESCENDING)], {"name": "idx_severity_score_desc"}),

    # Exact-match filters used alone or together
    ([("severity", ASCENDING)],  {"name": "idx_severity"}),
    ([("ioc_type", ASCENDING)],  {"name": "idx_ioc_type"}),
    ([("source", ASCENDING)],    {"name": "idx_source"}),

    # Compound: type + severity (IOC Explorer filters)
    (
        [("ioc_type", ASCENDING), ("severity", ASCENDING)],
        {"name": "idx_type_severity"},
    ),
    # Compound: source + severity_score (used in top-threats queries)
    (
        [("source", ASCENDING), ("severity_score", DESCENDING)],
        {"name": "idx_source_score"},
    ),
    # Compound: severity + score — covers /critical endpoint sort
    (
        [("severity", ASCENDING), ("severity_score", DESCENDING)],
        {"name": "idx_severity_score"},
    ),

    # Time-based queries (/recent endpoint, stats recent_count)
    ([("first_seen", DESCENDING)], {"name": "idx_first_seen_desc"}),

    # Unique lookup by IOC value (detail endpoint + dedup in seeder)
    (
        [("ioc_value", ASCENDING)],
        {"name": "idx_ioc_value", "unique": True, "sparse": True},
    ),

    # Full-text search across the three most useful fields
    (
        [
            ("ioc_value",      TEXT),
            ("description",    TEXT),
            ("malware_family", TEXT),
            ("tags",           TEXT),
        ],
        {"name": "idx_text_search", "default_language": "english"},
    ),

    # Demo-data cleanup marker
    ([("_demo", ASCENDING)], {"name": "idx_demo", "sparse": True}),
]


async def ensure_indexes() -> None:
    """Create all IOC collection indexes (idempotent — safe to call every startup)."""
    collection = db["iocs"]
    for spec, kwargs in _IOC_INDEXES:
        try:
            await collection.create_index(spec, **kwargs)
            logger.debug("Index ready: %s", kwargs.get("name"))
        except OperationFailure as exc:
            # Index already exists with different options — log and continue
            logger.warning("Index skipped (%s): %s", kwargs.get("name"), exc)
    logger.info("✅ MongoDB indexes verified.")


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
async def connect_db() -> None:
    """Open the Motor connection pool and verify connectivity."""
    global client, db
    try:
        client = AsyncIOMotorClient(
            MONGO_URI,
            # Pool sizing: Render free tier is single-process; keep it small
            maxPoolSize=10,
            minPoolSize=1,
            # Fail fast on startup rather than hanging
            serverSelectionTimeoutMS=8_000,
            connectTimeoutMS=8_000,
            socketTimeoutMS=15_000,
        )
        db = client[DB_NAME]
        await client.admin.command("ping")
        logger.info("✅ Connected to MongoDB (%s / %s)", MONGO_URI.split("@")[-1], DB_NAME)

        # Build indexes right after connecting so they exist before the first request
        await ensure_indexes()

    except ConnectionFailure as exc:
        logger.error("❌ MongoDB connection failed: %s", exc)
        raise


async def disconnect_db() -> None:
    """Close the Motor connection pool."""
    global client
    if client:
        client.close()
        logger.info("✅ Disconnected from MongoDB.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_database():
    return db


def get_collection(name: str):
    return db[name]


def get_db_client():
    return client
