# Pagination Notes

---

## 1. Offset-Based Pagination (current implementation)

```python
.skip((page - 1) * limit).limit(limit)
```

### How it works
- Client sends `?page=2&limit=10`
- MongoDB skips the first `(page-1) * limit` documents, then returns `limit` documents
- Simple to implement, supports random page access (`?page=5`)

### The bug (skipped/duplicate rows)
Happens when new documents are inserted between page requests:

```
Sort order: newest first (created_at desc)

User loads page 1 → [doc-10, doc-9, doc-8, doc-7, doc-6]
                                                     ^last seen

New doc-11 inserted

User loads page 2 → skip 5 → [doc-6, doc-5, doc-4, doc-3, doc-2]
                               ^ doc-6 appears AGAIN (duplicate)
                               ^ doc-11 was never seen (missed)
```

### When does it hurt?
- High insert rate (fuel station with many concurrent transactions)
- Large collections (100k+ records) — `skip()` gets slower as it scans all skipped docs
- Real-time dashboards where users paginate while data is being inserted

### Current status in this project
- Acceptable for now — admin list views, low concurrency
- Watch for it when transactions collection grows large

---

## 2. Cursor-Based Pagination (recommended at scale)

```python
# Page 1 — no cursor, just get first batch
.find({}).sort("_id", -1).limit(10)
# → returns docs, last doc has _id = "abc-123"

# Page 2 — pass that _id as cursor
.find({"_id": {"$lt": "abc-123"}}).sort("_id", -1).limit(10)
# → returns next batch after "abc-123", no skipping
```

### How it works
- Instead of "skip N rows", query "give me records before/after this specific ID"
- MongoDB uses the index directly — no scanning skipped docs
- No duplicates or missed rows regardless of concurrent inserts

### API contract change
```
# Old (offset)
GET /api/transactions/?page=2&limit=10

# New (cursor)
GET /api/transactions/?cursor=abc-123&limit=10
Response includes: { "next_cursor": "xyz-456", "has_more": true }
```

### Trade-offs
| Feature              | Offset         | Cursor         |
|----------------------|----------------|----------------|
| Random page access   | Yes (?page=5)  | No             |
| Duplicate-free       | No             | Yes            |
| Performance at scale | Degrades       | Constant       |
| Implementation       | Simple         | Moderate       |
| UI pattern           | Numbered pages | Infinite scroll / Load more |

### When to switch
- Transactions collection > 100k records
- Frontend uses "load more" instead of numbered pages
- Users report duplicate transactions in paginated views

### Opaque Cursors (professional standard)

Never expose raw internal values as the cursor. Always base64-encode it.

**Why opaque?**
- Client treats the cursor as a black box — just passes it back, no parsing
- Decouples your API contract from internal field names (`created_at`, `_id`, etc.)
- If you ever change the cursor field (e.g. from `created_at` to a compound value), no breaking API change
- Prevents clients from crafting arbitrary cursor values to probe your data
- Used by GitHub, Stripe, Twitter/X — industry standard

**Implementation pattern:**
```python
import base64
from datetime import datetime, timezone

# Encode before sending to client
def encode_cursor(dt: datetime) -> str:
    return base64.b64encode(dt.isoformat().encode()).decode()

# Decode when received from client
def decode_cursor(cursor: str) -> datetime:
    iso = base64.b64decode(cursor.encode()).decode()
    return datetime.fromisoformat(iso)
```

**API looks like:**
```
# First page (no cursor)
GET /api/transactions/?limit=10

# Next page (opaque cursor from previous response)
GET /api/transactions/?cursor=MjAyNS0wMS0xNVQxMDozMDowMC4wMDAwMDArMDA6MDA=&limit=10

# Response always includes
{ "next_cursor": "MjAyNS0wMS0x...", "has_more": true }
```

Client never knows `created_at` is the cursor field. You can change internals freely.

---

## 3. Which to use when

| Use case                        | Recommendation  |
|---------------------------------|-----------------|
| Admin list views, small data    | Offset (current) |
| Real-time transaction feed      | Cursor-based    |
| Export / report generation      | Cursor-based    |
| Numbered pagination UI          | Offset          |
| Infinite scroll / mobile app    | Cursor-based    |

---

## 4. Socket.IO — Interview Questions (Senior Level)

### Scaling
- What happens when you have 10,000 concurrent socket connections?
- How do you scale Socket.IO across multiple server instances?
- What is Redis adapter and why do you need it?

### Reliability
- What happens if the client loses connection mid-stream?
- How do you handle reconnection without missing events?
- What is acknowledgement (ack) in Socket.IO?

### Security
- How do you prevent a user from receiving another user's events?
- What is room-based isolation?
- How do you handle token expiry on a long-lived socket connection?

### Architecture
- When would you use raw WebSockets instead of Socket.IO?
- What is long-polling fallback and why does it exist?
- How does Socket.IO differ from Server-Sent Events (SSE)?

---

### What you already know (junior → mid level)
- Connection lifecycle (connect, disconnect, events)
- `emit()` vs `socketio.emit()` — reply vs broadcast
- Namespaces — isolating traffic per feature
- JWT auth on connect
- When to use socket vs REST API
- Persistent socket vs page-specific socket
- `request_init` pattern for on-demand refresh
