# Backend API (FastAPI) - Technical Explanation

## Overview

The backend is built with **FastAPI**, a modern, high-performance Python web framework that provides automatic API documentation, request/response validation, and async support. It serves as the central API layer between the frontend dashboard and the MongoDB database.

---

## 1. FastAPI Application (`main.py`)

### What It Does
`main.py` is the entry point for the entire backend API. It:
- Initializes the FastAPI application
- Configures middleware (CORS for cross-origin requests)
- Sets up database connections on startup/shutdown
- Registers API routers for different endpoints
- Provides automatic OpenAPI documentation

### How It Works

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to MongoDB
    await connect_db()
    yield
    # Shutdown: disconnect
    await disconnect_db()
```

**Lifespan Context Manager**: This is FastAPI's modern way of handling startup/shutdown events. It ensures MongoDB connects when the server starts and disconnects cleanly when it stops.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**CORS Middleware**: Allows the React frontend (running on port 3000) to make requests to the backend (port 8000). Without this, browsers would block the requests due to same-origin policy.

```python
app.include_router(threats.router, prefix="/api/threats", tags=["Threats"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
```

**Router Registration**: FastAPI uses a modular router pattern. Each router handles a specific domain (threats, analytics, datasets), keeping code organized.

### Why This Approach?

1. **FastAPI over Flask**: 
   - **Performance**: Built on Starlette and Pydantic, FastAPI is 2-3x faster than Flask
   - **Async Support**: Native async/await for non-blocking database calls
   - **Auto Documentation**: Generates OpenAPI (Swagger) docs automatically at `/docs`
   - **Type Safety**: Pydantic models validate requests/responses at runtime

2. **Async Database Calls**: Using Motor (async MongoDB driver) allows handling thousands of concurrent requests without blocking

3. **Automatic Validation**: Pydantic models catch invalid data before it reaches your code

### Common Viva Questions

**Q: Why FastAPI instead of Flask or Django?**
- **Answer**: FastAPI provides automatic API documentation, request validation with Pydantic, and native async support for high-performance database operations. Flask doesn't have built-in async or validation; Django is too heavy for an API-only service.

**Q: What is CORS and why do you need it?**
- **Answer**: CORS (Cross-Origin Resource Sharing) allows the React frontend (localhost:3000) to make requests to the backend API (localhost:8000). Browsers block cross-origin requests by default for security, so we explicitly allow our frontend origin.

**Q: What happens if MongoDB connection fails at startup?**
- **Answer**: The `connect_db()` function raises a `ConnectionFailure` exception, which prevents the FastAPI app from starting. This fail-fast approach ensures we don't serve requests without database access.

---

## 2. Database Layer (`database.py`)

### What It Does
Manages the MongoDB connection lifecycle using **Motor** (async MongoDB driver). Provides helper functions to access collections.

### How It Works

```python
client: AsyncIOMotorClient = None
db = None

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    await client.admin.command('ping')
    print(f"✅ Connected to MongoDB at {MONGO_URI}")
```

**Global Client Pattern**: We maintain a single MongoDB client instance across the application. Creating a new client for each request would be extremely inefficient.

**Connection Ping**: `client.admin.command('ping')` verifies the connection is actually alive, not just that the client object was created.

```python
def get_collection(name: str):
    return db[name]
```

**Collection Access**: This helper function provides a clean way to access MongoDB collections in routers without importing `db` directly.

### Why This Approach?

1. **Motor over PyMongo**: Motor is the async version of PyMongo. Using async I/O prevents blocking when waiting for database responses, critical for high-concurrency APIs.

2. **Connection Pooling**: Motor automatically manages a connection pool, reusing connections across requests for efficiency.

3. **Environment Configuration**: `MONGO_URI` is read from environment variables, allowing different configurations for development (`localhost:27017`) and production (`mongo:27017` in Docker).

### Common Viva Questions

**Q: What is Motor and why use it over PyMongo?**
- **Answer**: Motor is the async version of PyMongo. It allows non-blocking database operations with async/await, which is essential for FastAPI's async endpoints. PyMongo would block the event loop and reduce performance under load.

**Q: Why use a global database client instead of creating one per request?**
- **Answer**: Creating a MongoDB client is expensive (requires network handshake, authentication). A global client with connection pooling reuses connections, improving performance by 10-100x.

**Q: How does connection pooling work?**
- **Answer**: Motor maintains a pool of open connections to MongoDB. When a request needs the database, it borrows a connection from the pool. After the query completes, the connection returns to the pool for reuse. This avoids the overhead of opening/closing connections for each request.

---

## 3. Data Models (`models.py`)

### What It Does
Defines **Pydantic models** that validate and serialize API request/response data. These act as both documentation and runtime validators.

### How It Works

```python
class ThreatType(str, Enum):
    CREDENTIAL_LEAK = "credential_leak"
    EXPLOIT = "exploit"
    PHISHING = "phishing"
    MALWARE = "malware"
    UNKNOWN = "unknown"
```

**Enum Classes**: Restricts threat types to predefined values. If a request sends `"invalid_type"`, Pydantic automatically rejects it with a 422 error.

```python
class ThreatRecord(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    dataset: DatasetSource
    threat_type: ThreatType
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None
    classification_confidence: Optional[float] = None

    class Config:
        populate_by_name = True
```

**Field Aliases**: MongoDB uses `_id` for the document ID, but Python conventionally uses `id`. The alias allows both to work seamlessly.

**Default Factories**: `default_factory=datetime.utcnow` ensures each record gets the current timestamp when created (not when the class is defined).

**Config Options**: `populate_by_name=True` allows accepting both `id` and `_id` in requests.

### Why This Approach?

1. **Type Safety**: Pydantic validates types at runtime. If the frontend sends `confidence: "high"` instead of `0.92`, it's rejected before reaching your code.

2. **Auto Documentation**: FastAPI reads these models to generate the OpenAPI schema, showing exactly what fields each endpoint expects/returns.

3. **Serialization**: Pydantic automatically converts MongoDB documents (dict) to JSON-safe formats (e.g., converting `datetime` objects to ISO strings).

### Common Viva Questions

**Q: What is Pydantic and why use it?**
- **Answer**: Pydantic is a data validation library using Python type hints. It validates incoming requests, converts data types, and generates JSON schemas for documentation—all automatically. This prevents bugs from invalid data and reduces boilerplate code.

**Q: Why use Enum for ThreatType instead of plain strings?**
- **Answer**: Enums provide compile-time and runtime validation. If code tries to use an invalid threat type, it fails immediately. Plain strings could allow typos like "phising" to slip through unnoticed.

**Q: What is `Field(default_factory=datetime.utcnow)`?**
- **Answer**: `default_factory` calls a function to generate the default value each time a model is created. Using `default=datetime.utcnow()` would set all records to the same timestamp (when the class loads), not when each record is created.

---

## 4. Threats Router (`routers/threats.py`)

### What It Does
Handles all threat-related endpoints: listing threats, getting individual threats, and searching by content.

### How It Works

```python
@router.get("/", response_model=List[ThreatRecord])
async def get_threats(
    limit: int = Query(100, ge=1, le=1000),
    threat_type: Optional[ThreatType] = None,
    dataset: Optional[DatasetSource] = None
):
```

**Query Parameters with Validation**: `Query(100, ge=1, le=1000)` means:
- Default limit is 100
- `ge=1`: Must be >= 1
- `le=1000`: Must be <= 1000

If a request sends `?limit=5000`, FastAPI rejects it automatically.

```python
query = {}
if threat_type:
    query["threat_type"] = threat_type.value
if dataset:
    query["dataset"] = dataset.value

cursor = collection.find(query).limit(limit).sort("timestamp", -1)
```

**Dynamic Query Building**: Builds a MongoDB query dict based on which filters the user provided. Only filters that are present are added to the query.

**Cursor Pattern**: `.find()` returns a cursor (lazy iterator), not all results at once. `.limit()` and `.sort()` are efficient MongoDB operations.

```python
@router.get("/search/content")
async def search_threats(
    q: str = Query(..., min_length=3),
```

**Text Search**: Uses MongoDB's full-text search with text indexes on the `content` field. This allows searching for keywords across all threat descriptions efficiently.

### Why This Approach?

1. **Query Parameter Validation**: FastAPI automatically validates limits, preventing abuse (e.g., requesting 10 million records).

2. **Async Database Calls**: `await collection.find()` allows handling multiple concurrent requests without blocking.

3. **Pagination**: The `limit` parameter enables pagination, crucial for UIs that display data in chunks.

### Common Viva Questions

**Q: Why use query parameters instead of POST body for filtering?**
- **Answer**: Query parameters are RESTful convention for GET requests (which should be idempotent and cacheable). POST bodies are for creating/updating resources. Filters like `?threat_type=phishing` are semantic and browser-bookmarkable.

**Q: What is a MongoDB cursor and why use it?**
- **Answer**: A cursor is a pointer to the result set. Instead of loading all 1 million threats into memory, the cursor streams results as needed. Combined with `.limit()`, we only fetch the requested number of documents, saving memory and bandwidth.

**Q: How does text search work in MongoDB?**
- **Answer**: MongoDB's text search uses inverted indexes (like search engines). When you create a text index on the `content` field, MongoDB tokenizes and indexes words. Searches use this index for fast keyword lookups, even across millions of documents.

---

## 5. Analytics Router (`routers/analytics.py`)

### What It Does
Provides aggregated statistics and trends: total threats, breakdowns by type/dataset, and recent threat samples.

### How It Works

```python
@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary():
    threats_col = get_collection("threats")
    
    total = await threats_col.count_documents({})
```

**Count Documents**: Efficient way to get the total count without loading all documents.

```python
pipeline_type = [
    {"$group": {"_id": "$threat_type", "count": {"$sum": 1}}}
]
type_agg = await threats_col.aggregate(pipeline_type).to_list(length=None)
threats_by_type = {item["_id"]: item["count"] for item in type_agg}
```

**Aggregation Pipeline**: MongoDB's aggregation framework is like SQL's GROUP BY. This pipeline:
1. `$group`: Groups all documents by `threat_type`
2. `$sum: 1`: Counts documents in each group

Result: `{"credential_leak": 150000, "phishing": 80000, ...}`

```python
recent = await threats_col.find().sort("timestamp", -1).limit(10).to_list(length=10)
```

**Recent Threats**: Gets the 10 most recent threats (sorted by timestamp descending).

### Why This Approach?

1. **Aggregation over Client-Side Processing**: Running aggregations in MongoDB is 100x faster than fetching all data and processing it in Python. MongoDB executes aggregations near the data (in C++), minimizing data transfer.

2. **Separate Analytics Endpoint**: Aggregations can be slow on large datasets. Isolating them in `/analytics/summary` allows caching and prevents blocking the main threat listing endpoint.

### Common Viva Questions

**Q: What is MongoDB aggregation and why use it?**
- **Answer**: Aggregation is MongoDB's framework for data processing pipelines (like SQL's GROUP BY, JOIN, etc.). It runs on the database server, processing data efficiently without transferring millions of records to the application. For example, grouping 500,000 threats by type happens in milliseconds with aggregation, versus minutes if done in Python.

**Q: Could you do this with multiple simple queries instead of aggregation?**
- **Answer**: Yes, but it would be much slower. For threat counts by type, you'd need 5 separate `count_documents()` calls (one per type). Aggregation does it in one optimized query with a single database round-trip.

**Q: Why limit recent threats to 10 instead of 100?**
- **Answer**: The summary endpoint is called frequently (every 30s by the dashboard). Limiting to 10 reduces payload size and query time. If users want more, they can use the paginated `/api/threats` endpoint.

---

## 6. Datasets Router (`routers/datasets.py`)

### What It Does
Provides dataset-level metadata: ingestion status, threat counts per dataset, and ingestion logs.

### How It Works

```python
@router.get("/status")
async def get_dataset_status():
    pipeline = [
        {"$group": {
            "_id": "$dataset",
            "total_threats": {"$sum": 1},
            "threat_types": {"$addToSet": "$threat_type"},
            "latest_timestamp": {"$max": "$timestamp"}
        }},
        {"$project": {
            "dataset": "$_id",
            "total_threats": 1,
            "unique_threat_types": {"$size": "$threat_types"},
            "latest_update": "$latest_timestamp",
            "_id": 0
        }},
        {"$sort": {"total_threats": -1}}
    ]
```

**Complex Aggregation Pipeline**:
1. `$group`: Groups threats by dataset, accumulating:
   - Total count
   - Unique threat types (using `$addToSet` to collect unique values)
   - Latest timestamp
2. `$project`: Reshapes the output, calculates array size for unique types
3. `$sort`: Orders datasets by threat count (descending)

Result:
```json
{
  "datasets": [
    {
      "dataset": "phishing_emails",
      "total_threats": 201048,
      "unique_threat_types": 3,
      "latest_update": "2025-10-30T06:25:58"
    },
    ...
  ]
}
```

### Why This Approach?

1. **Real-Time Aggregation**: Instead of storing dataset counts in a separate table, we aggregate from the source of truth (`threats` collection). This ensures counts are always accurate, even if ingestion runs multiple times.

2. **Additive Set Operations**: `$addToSet` efficiently tracks unique threat types without duplicates, similar to Python's `set()`.

### Common Viva Questions

**Q: Why aggregate dataset stats instead of storing them during ingestion?**
- **Answer**: Aggregation ensures consistency. If you store counts and ingestion fails halfway, counts become stale. Aggregating from the `threats` collection guarantees accuracy, and MongoDB makes it fast enough for real-time queries.

**Q: What does `$addToSet` do?**
- **Answer**: `$addToSet` accumulates unique values into an array (like Python's `set.add()`). For each threat in a dataset, it adds the threat type to the set, automatically deduplicating. We then use `$size` to count unique types.

---

## 7. API Endpoints Summary

| Endpoint | Method | Description | Key Query Params |
|----------|--------|-------------|------------------|
| `/` | GET | API health check | - |
| `/health` | GET | Service health status | - |
| `/api/threats` | GET | List threats with filters | `limit`, `threat_type`, `dataset` |
| `/api/threats/{id}` | GET | Get single threat by ID | - |
| `/api/threats/search/content` | GET | Full-text search | `q` (min 3 chars), `limit` |
| `/api/analytics/summary` | GET | Overall statistics | - |
| `/api/analytics/trends` | GET | Time-series trends | - |
| `/api/datasets/status` | GET | Dataset-level stats | - |
| `/api/datasets/logs` | GET | Ingestion run history | `limit` |

---

## 8. Error Handling

### HTTP Exception Handling

```python
@router.get("/{threat_id}", response_model=ThreatRecord)
async def get_threat_by_id(threat_id: str):
    try:
        threat = await collection.find_one({"_id": ObjectId(threat_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid threat ID format")
    
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
```

**Graceful Error Responses**: FastAPI catches `HTTPException` and returns proper JSON error responses:

```json
{
  "detail": "Threat not found"
}
```

### Automatic Validation Errors

If a request violates Pydantic model constraints, FastAPI returns a 422 error with detailed field-level errors:

```json
{
  "detail": [
    {
      "loc": ["query", "limit"],
      "msg": "ensure this value is less than or equal to 1000",
      "type": "value_error.number.not_le"
    }
  ]
}
```

### Common Viva Questions

**Q: Why return 404 vs 400 for missing threats?**
- **Answer**: HTTP status codes are semantic. 400 (Bad Request) means the request itself is malformed (invalid ID format). 404 (Not Found) means the request was valid but the resource doesn't exist. This follows REST conventions.

**Q: What happens if MongoDB is down when a request comes in?**
- **Answer**: Motor will raise a `ConnectionFailure` or `ServerSelectionTimeoutError`. FastAPI catches unhandled exceptions and returns a 500 Internal Server Error. In production, you'd want custom error handlers to log these and return user-friendly messages.

---

## 9. Performance Optimizations

### 1. Async I/O
All database calls use `await`, allowing the server to handle other requests while waiting for MongoDB responses.

### 2. Database Indexes
While not visible in code, MongoDB indexes on `timestamp`, `threat_type`, and `dataset` fields are critical for query performance:

```python
# Would be created via MongoDB shell or migration script
db.threats.create_index([("timestamp", -1)])
db.threats.create_index([("threat_type", 1)])
db.threats.create_index([("dataset", 1)])
db.threats.create_index([("content", "text")])  # For text search
```

### 3. Query Limits
All list endpoints enforce maximum limits to prevent memory exhaustion from requesting millions of records.

### Common Viva Questions

**Q: How does async improve performance?**
- **Answer**: Traditional synchronous code blocks while waiting for I/O (database, network). With async, when one request waits for MongoDB, the server can process other requests. This allows handling 10,000+ concurrent connections on a single server.

**Q: What database indexes did you create and why?**
- **Answer**: We indexed `timestamp` (for sorting recent threats), `threat_type` and `dataset` (for filtered queries), and `content` (for text search). Without indexes, queries on 500k+ documents would scan every record (slow). Indexes turn O(n) scans into O(log n) lookups.

---

## 10. API Documentation (Auto-Generated)

FastAPI automatically generates interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These are generated from:
- Pydantic models (request/response schemas)
- Docstrings (endpoint descriptions)
- Type hints (parameter types)

No extra work needed—FastAPI reads your code and builds the docs.

### Common Viva Questions

**Q: How does FastAPI generate docs automatically?**
- **Answer**: FastAPI uses Python introspection to read type hints, Pydantic models, and docstrings from your code. It converts these into an OpenAPI 3.0 specification (JSON), which Swagger UI/ReDoc render as interactive HTML. You write typed Python code; docs come free.

---

## Key Takeaways for Viva

1. **FastAPI Choice**: High performance, async support, auto validation, auto docs
2. **Motor over PyMongo**: Async MongoDB driver prevents blocking under load
3. **Pydantic Models**: Runtime validation + auto documentation + serialization
4. **Aggregation Pipelines**: Process data in MongoDB (fast) vs Python (slow)
5. **CORS Middleware**: Required for frontend-backend communication across ports
6. **Error Handling**: Semantic HTTP status codes (400/404/422/500)
7. **Indexes**: Critical for query performance on large collections
8. **Async Patterns**: Non-blocking I/O for high concurrency

---

**Next**: [03_ingestion_service.md](./03_ingestion_service.md) - How data flows from files into Kafka
