# Fuel Tracking System

A Fuel Tracking System where employees log fuel transactions at specific pumps for vehicles. It provides a real-time central dashboard that updates instantly using MongoDB Change Streams and Socket.IO. Built with Python Flask for the backend and MongoDB as the database.

## Tech Stack

- **Backend:** Python, Flask
- **Database:** MongoDB (via Flask-PyMongo)
- **Real-time:** Socket.IO (flask-socketio, gevent)
- **Auth:** JWT (PyJWT)
- **Validation:** Marshmallow
- **Rate Limiting:** Flask-Limiter
- **Migrations:** pymongo-migrate

---

## Setup

### 1. Clone and create virtual environment

```bash
git clone <repo-url>
cd fuel-tracking-system
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file in the root:

```env
MONGO_URI=mongodb://localhost:27017/fuel_tracking
SECRET_KEY=your-secret-key-at-least-32-chars
JWT_ACCESS_EXPIRY_MINUTES=15
JWT_REFRESH_EXPIRY_DAYS=7
DEBUG=false
PORT=5000
```

### 4. Run migrations

```bash
python migrate.py
```

### 5. Run the server

```bash
python run.py
```

Server runs at `http://localhost:5000`

### 6. Run tests

```bash
venv\Scripts\python -m pytest tests/ -v
```

---

## Authentication

All protected endpoints require an access token in the header:

```
Authorization: Bearer <access_token>
```

Obtain tokens via `POST /api/auth/login`. Access tokens expire after 15 minutes. Use `POST /api/auth/refresh` with your refresh token to get a new access token. Use `POST /api/auth/logout` to invalidate the refresh token.

> There is no self-registration. All user accounts must be created by an admin via `POST /api/users/`.

---

## Roles

| Role | Scope | Description |
|------|-------|-------------|
| `admin` | Global | Full access — create pumps, users, fuel prices, view all data |
| `employee` | Global | Can record transactions, search vehicles |
| `pump_admin` | Pump-scoped | Can add/remove employees for their assigned pump |

> `pump_admin` is not a global role — it is stored in `pump_employees` collection per pump.

---

## Schema

### User
| Field | Type | Description |
|-------|------|-------------|
| _id | string (uuid) | Primary key |
| name | string | Full name |
| email | string | Unique email |
| password_hash | string | Hashed password (never returned in responses) |
| role | string | `admin` or `employee` |
| refresh_token | string | Active refresh token (never returned in responses) |
| refresh_token_expires_at | datetime | Refresh token expiry (never returned in responses) |
| created_at | datetime | Creation timestamp |

### Vehicle
| Field | Type | Description |
|-------|------|-------------|
| _id | string (uuid) | Primary key |
| vehicle_number | string | Unique plate number (case-insensitive) |
| created_at | datetime | Creation timestamp |

### Pump
| Field | Type | Description |
|-------|------|-------------|
| _id | string (uuid) | Primary key |
| name | string | Station name |
| location | string | Station location |
| license | string | Unique pump license |
| created_at | datetime | Creation timestamp |

### PumpEmployee
| Field | Type | Description |
|-------|------|-------------|
| _id | string (uuid) | Primary key |
| pump_id | string | FK → Pump |
| user_id | string | FK → User |
| role | string | `pump_admin` or `employee` (pump-scoped) |
| added_by | string | FK → User who added this record |
| created_at | datetime | Creation timestamp |

> Compound unique index on `(pump_id, user_id)` — one record per user per pump.
> Only one `pump_admin` allowed per pump.

### FuelPrice
| Field | Type | Description |
|-------|------|-------------|
| _id | string (uuid) | Primary key |
| fuel_type | string | `octane`, `diesel`, `petrol` |
| price_per_unit | float | Price per unit |
| unit | string | `liter`, `gallon` |
| currency | string | `BDT`, `USD`, `EUR`, `GBP` (default: BDT) |
| effective_from | string | Date `YYYY-MM-DD` |
| created_at | datetime | Creation timestamp |

### Transaction
| Field | Type | Description |
|-------|------|-------------|
| _id | string (uuid) | Primary key |
| vehicle_id | string | FK → Vehicle |
| pump_id | string | FK → Pump |
| fuel_price_id | string | FK → FuelPrice |
| quantity | float | Amount of fuel (in FuelPrice unit), stored at 4 decimal precision |
| total_price | float | Total cost snapshot, stored at 4 decimal precision |
| created_at | datetime | Creation timestamp |

> `fuel_type`, `unit`, and `currency` are not stored on Transaction — accessed via `fuel_price_id` join.

---

## Relations

```
Vehicle         ──< Transaction
Pump            ──< Transaction
Pump            ──< PumpEmployee
User            ──< PumpEmployee
FuelPrice       ──< Transaction
```

---

## API Reference

All responses follow this structure:

```json
// Success
{ "status": 200, "message": "...", "data": { ... } }

// Created
{ "status": 201, "message": "...", "data": { ... } }

// Paginated (cursor-based)
{
  "status": 200,
  "message": "...",
  "data": {
    "<key>": [...],
    "pagination": {
      "limit": 10,
      "next_cursor": "<base64-opaque-string or null>",
      "has_more": true
    }
  }
}

// Error
{ "status": 4xx, "message": "...", "errors": { ... } }
```

> **Pagination** uses cursor-based pagination. Pass `?cursor=<next_cursor>` from the previous response to get the next page. `has_more: false` means you're on the last page.

---

### Auth

#### `POST /api/auth/login`
Login and receive tokens.

**Auth required:** No

**Request body:**
```json
{ "email": "user@example.com", "password": "secret123" }
```

**Response `200`:**
```json
{ "access_token": "...", "refresh_token": "...", "token_type": "Bearer" }
```

**Other responses:** `400 Validation failed` / `401 Invalid credentials`

---

#### `POST /api/auth/refresh`
Get a new access token using a refresh token.

**Auth required:** No

**Request body:**
```json
{ "refresh_token": "..." }
```

**Response `200`:**
```json
{ "access_token": "...", "token_type": "Bearer" }
```

**Other responses:** `400 refresh_token required` / `401 Invalid or expired`

---

#### `POST /api/auth/logout`
Invalidate the refresh token.

**Auth required:** Yes (Bearer access token)

**Request body:**
```json
{ "refresh_token": "..." }
```

**Responses:** `200` / `400` / `401`

---

### Users

#### `POST /api/users/`
Create a new user.

**Auth required:** `admin`

**Request body:**
```json
{ "name": "John Doe", "email": "user@example.com", "password": "secret123", "role": "employee" }
```

**Validation:**
- `name`: required, 2–100 characters
- `email`: required, valid email format
- `password`: required, minimum 8 characters
- `role`: optional, defaults to `employee` — one of `admin`, `employee`

**Responses:** `201` / `400` / `401` / `403` / `409 Email already exists`

---

#### `GET /api/users/`
Get all users (paginated).

**Auth required:** `admin`

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Page size (default: 10, max: 100) |
| `cursor` | string | No | Opaque cursor from previous response |
| `role` | string | No | Filter by role: `admin`, `employee` |
| `name` | string | No | Filter by name (partial match, case-insensitive) |
| `email` | string | No | Filter by email (partial match, case-insensitive) |

**Responses:** `200` / `400` / `401` / `403`

---

#### `GET /api/users/me`
Get the currently authenticated user's profile.

**Auth required:** Any authenticated user

**Responses:** `200` / `401` / `404`

---

#### `GET /api/users/<user_id>`
Get a single user by ID.

**Auth required:** Any authenticated user

**Response details:**
- Includes `pump_role`, which is the user's assignment role for their current pump (`employee` or `pump_admin`) or `null` if not assigned.

**Responses:** `200` / `401` / `404`

---

#### `PATCH /api/users/<user_id>`
Update a user.

**Auth required:** `admin`

**Request body:** Any subset of `name`, `role`

**Validation:**
- `name`: 2–100 characters
- `role`: one of `admin`, `employee`

**Responses:** `200` / `400` / `401` / `403` / `404`

---

#### `DELETE /api/users/<user_id>`
Delete a user and cascade-delete their pump assignments.

**Auth required:** `admin`

**Responses:** `200` / `401` / `403` / `404`

---

### Vehicles

#### `POST /api/vehicles/`
Create a new vehicle.

**Auth required:** Any authenticated user (`admin` or `employee`)

**Request body:**
```json
{ "vehicle_number": "DH-1234" }
```

**Validation:**
- `vehicle_number`: required, 2–10 characters

**Responses:** `201` / `400` / `401` / `409 Vehicle number already exists`

---

#### `GET /api/vehicles/`
Get all vehicles (paginated).

**Auth required:** `admin`

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Page size (default: 10, max: 100) |
| `cursor` | string | No | Opaque cursor from previous response |
| `search` | string | No | Partial, case-insensitive match on `vehicle_number` |

**Responses:** `200` / `400` / `401` / `403`

---

#### `GET /api/vehicles/<vehicle_id>`
Get a single vehicle by ID.

**Auth required:** Any authenticated user

**Responses:** `200` / `401` / `404`

---

#### `GET /api/vehicles/search`
Search vehicles by number (for autocomplete).

**Auth required:** `admin` or `employee`

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `q` | string | Yes | Partial, case-insensitive match on `vehicle_number` |
| `limit` | int | No | Max results (default: 10, max: 100) |

**Responses:** `200` / `400 Missing q` / `401` / `403`

---

#### `PATCH /api/vehicles/<vehicle_id>`
Update a vehicle.

**Auth required:** `admin`

**Request body:** Any subset of `vehicle_number`

**Validation:**
- `vehicle_number`: 2–10 characters

**Responses:** `200` / `400` / `401` / `403` / `404`

---

#### `DELETE /api/vehicles/<vehicle_id>`
Delete a vehicle.

**Auth required:** `admin`

**Responses:** `200` / `401` / `403` / `404`

---

### Pumps

#### `POST /api/pumps/`
Create a new pump.

**Auth required:** `admin`

**Request body:**
```json
{ "name": "Shell Dhaka", "location": "Mirpur", "license": "P-001" }
```

**Responses:** `201` / `400` / `401` / `403` / `409 License already exists`

---

#### `GET /api/pumps/`
Get all pumps (paginated).

**Auth required:** Any authenticated user

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Page size (default: 10, max: 100) |
| `cursor` | string | No | Opaque cursor from previous response |
| `name` | string | No | Filter by name (partial match, case-insensitive) |
| `location` | string | No | Filter by location (partial match, case-insensitive) |
| `license` | string | No | Filter by license (partial match, case-insensitive) |

**Responses:** `200` / `400` / `401`

---

#### `GET /api/pumps/<pump_id>`
Get a single pump by ID.

**Auth required:** Any authenticated user

**Responses:** `200` / `401` / `404`

---

#### `PATCH /api/pumps/<pump_id>`
Update a pump.

**Auth required:** `admin`

**Request body:** Any subset of `name`, `location`, `license`

**Responses:** `200` / `400` / `401` / `403` / `404` / `409 License already exists`

---

#### `DELETE /api/pumps/<pump_id>`
Delete a pump and cascade-delete all its employee assignments.

**Auth required:** `admin`

**Responses:** `200` / `401` / `403` / `404`

---

### Pump Employees

#### `GET /api/pumps/me/pump`
Get the pump assignment for the currently authenticated user.

**Auth required:** `employee` or `admin`

**Responses:** `200` / `401` / `403` / `404 No pump assignment found`

---

#### `POST /api/pumps/<pump_id>/employees`
Add an employee to a pump.

**Auth required:** Global `admin` OR `pump_admin` of this pump

**Request body (existing user):**
```json
{ "mode": "existing", "email": "employee@example.com", "role": "employee" }
```

**Request body (create new user + assign):**
```json
{
  "mode": "new",
  "name": "New Employee",
  "email": "new.employee@example.com",
  "password": "secret123",
  "role": "employee"
}
```

> `role` must be `pump_admin` or `employee`. Only one `pump_admin` allowed per pump.
> In `new` mode, a platform user is created first with global role `employee`, then assigned to the pump.
> An employee can only be assigned to one pump at a time.
> Only global `admin` can create a brand-new `pump_admin` in `new` mode.

**Responses:** `201` / `400` / `401` / `403` / `404` / `409 Already assigned or user already exists in new mode`

---

#### `DELETE /api/pumps/<pump_id>/employees/<user_id>`
Remove an employee from a pump.

**Auth required:** Global `admin` OR `pump_admin` of this pump

> `pump_admin` cannot remove another `pump_admin` — admin must do it.

**Responses:** `200` / `400` / `401` / `403` / `404`

---

#### `PATCH /api/pumps/<pump_id>/employees/<user_id>`
Update an employee's pump-scoped role.

**Auth required:** Global `admin` OR `pump_admin` of this pump

**Request body:**
```json
{ "role": "pump_admin" }
```

**Responses:** `200` / `400` / `401` / `403` / `404`

---

#### `GET /api/pumps/<pump_id>/employees`
List all employees of a pump (paginated).

**Auth required:** Global `admin` OR any employee assigned to this pump

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Page size (default: 10, max: 100) |
| `cursor` | string | No | Opaque cursor from previous response |

**Responses:** `200` / `400` / `401` / `404`

---

### Fuel Prices

#### `POST /api/fuel-prices/`
Create a new fuel price entry.

**Auth required:** `admin`

**Request body:**
```json
{
  "fuel_type": "octane",
  "price_per_unit": 125.0,
  "unit": "liter",
  "currency": "BDT",
  "effective_from": "2025-01-01"
}
```

**Validation:**
- `fuel_type`: required, one of `octane`, `diesel`, `petrol`
- `price_per_unit`: required, minimum `0.1`
- `unit`: required, one of `liter`, `gallon`
- `currency`: optional, one of `BDT`, `USD`, `EUR`, `GBP` — defaults to `BDT`
- `effective_from`: required, format `YYYY-MM-DD`

**Responses:** `201` / `400` / `401` / `403`

---

#### `GET /api/fuel-prices/`
Get all fuel prices (paginated).

**Auth required:** Any authenticated user

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Page size (default: 10, max: 100) |
| `cursor` | string | No | Opaque cursor from previous response |
| `fuel_type` | string | No | Filter by fuel type: `octane`, `diesel`, `petrol` |
| `effective_from` | string | No | Exact date match (YYYY-MM-DD). Ignored if range params are provided |
| `effective_from_after` | string | No | Filter prices effective on or after this date (YYYY-MM-DD) |
| `effective_from_before` | string | No | Filter prices effective on or before this date (YYYY-MM-DD) |

**Responses:** `200` / `400` / `401`

---

#### `GET /api/fuel-prices/<fuel_price_id>`
Get a single fuel price by ID.

**Auth required:** Any authenticated user

**Responses:** `200` / `401` / `404`

---

#### `GET /api/fuel-prices/latest/<fuel_type>`
Get the latest active price for a fuel type.

**Auth required:** Any authenticated user

**Example:** `GET /api/fuel-prices/latest/octane`

**Responses:** `200` / `401` / `404 No fuel price found`

---

### Transactions

#### `POST /api/transactions/`
Record a fuel transaction.

**Auth required:** `admin` or `employee` assigned to the pump

**Request body — quantity mode:**
```json
{
  "vehicle_number": "DH-1234",
  "pump_id": "...",
  "fuel_type": "octane",
  "quantity": 10.0
}
```

**Request body — amount mode:**
```json
{
  "vehicle_number": "DH-1234",
  "pump_id": "...",
  "fuel_type": "octane",
  "total_price": 400.0
}
```

**Validation:**
- `vehicle_number`: required, 2–10 characters
- `pump_id`: required
- `fuel_type`: required, one of `octane`, `diesel`, `petrol`
- `quantity` or `total_price`: exactly one must be provided — not both, not neither
  - `quantity`: minimum `0.1`
  - `total_price`: minimum `0.01`

> The server derives the missing field: quantity mode → `total_price = quantity × rate`; amount mode → `quantity = total_price / rate`. Both are stored at 4 decimal precision. The vehicle is auto-created if it doesn't exist. Uses a MongoDB transaction for atomicity.

**Responses:** `201` / `400` / `401` / `403` / `404 Pump/FuelPrice not found`

---

#### `GET /api/transactions/`
Get all transactions (paginated).

**Auth required:** `admin`

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Page size (default: 10, max: 100) |
| `cursor` | string | No | Opaque cursor from previous response |
| `vehicle_number` | string | No | Filter by vehicle number (partial match, case-insensitive) |
| `pump_name` | string | No | Filter by pump name (partial match, case-insensitive) |
| `pump_license` | string | No | Filter by pump license (exact match) |
| `fuel_type` | string | No | Filter by fuel type: `octane`, `diesel`, `petrol` |
| `from` | string | No | Start date filter `YYYY-MM-DD`. If omitted, defaults to `2000-01-01` |
| `to` | string | No | End date filter `YYYY-MM-DD`. If omitted, defaults to today |

**Responses:** `200` / `400` / `401` / `403`

> All transaction responses include enriched fields: `vehicle_number`, `pump_name`, `fuel_type`, `unit`, `currency`.

---

#### `GET /api/transactions/<transaction_id>`
Get a single transaction by ID.

**Auth required:** `admin` or pump employee assigned to the transaction's pump

**Responses:** `200` / `401` / `403` / `404`

---

#### `GET /api/transactions/vehicle/<vehicle_id>`
Get all transactions for a vehicle (paginated).

**Auth required:** Any authenticated user

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Page size (default: 10, max: 100) |
| `cursor` | string | No | Opaque cursor from previous response |
| `fuel_type` | string | No | Filter by fuel type: `octane`, `diesel`, `petrol` |
| `from` | string | No | Start date filter `YYYY-MM-DD`. If omitted, defaults to `2000-01-01` |
| `to` | string | No | End date filter `YYYY-MM-DD`. If omitted, defaults to today |

**Responses:** `200` / `400` / `401` / `404 Vehicle not found`

---

#### `GET /api/transactions/pump/<pump_id>`
Get all transactions for a pump (paginated).

**Auth required:** Global `admin` OR any employee assigned to this pump

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Page size (default: 10, max: 100) |
| `cursor` | string | No | Opaque cursor from previous response |
| `fuel_type` | string | No | Filter by fuel type: `octane`, `diesel`, `petrol` |
| `from` | string | No | Start date filter `YYYY-MM-DD`. If omitted, defaults to `2000-01-01` |
| `to` | string | No | End date filter `YYYY-MM-DD`. If omitted, defaults to today |

**Responses:** `200` / `400` / `401` / `403` / `404 Pump not found`

---

## Real-time (Socket.IO)

Connect to namespace `/dashboard`. A valid access token **must** be passed in the `auth` object on connect, otherwise the connection will be rejected.

**Access rules:**
- Global `admin`: allowed, receives all pumps data.
- Pump-scoped `pump_admin` (from `pump_employees`): allowed, receives only assigned pump data.
- Regular `employee` (not pump admin): connection is rejected.

```javascript
const socket = io('http://localhost:5000/dashboard', {
  auth: { token: '<access_token>' }
});
```

### Events sent from client

| Event | Payload | Description |
|-------|---------|-------------|
| `request_init` | none | Request fresh stats + transactions (use when navigating back to dashboard without reconnecting) |

### Events received from server

| Event | Payload | Description |
|-------|---------|-------------|
| `init` | `{ stats, transactions[] }` | Sent on connect or in response to `request_init`. Admin gets global last 20 + global stats; pump admin gets last 20 for assigned pump + pump-scoped stats |
| `new_transaction` | `{ transaction, stats }` | Real-time insert event. Admin receives all transactions; pump admin receives only transactions for assigned pump |

### Stats object
```json
{
  "total_transactions": 120,
  "total_fuel_dispensed": 1500.5,
  "total_revenue": 187562.5,
  "fuel_type_totals": {
    "octane": 520.0,
    "diesel": 710.5,
    "petrol": 270.0
  }
}
```

### Transaction object (enriched)

Transactions in both `init` and `new_transaction` events are enriched server-side:

```json
{
  "_id": "...",
  "vehicle_id": "...",
  "pump_id": "...",
  "fuel_price_id": "...",
  "quantity": 10.0,
  "total_price": 1250.0,
  "created_at": "2025-01-01T00:00:00",
  "fuel_type": "octane",
  "unit": "liter",
  "currency": "BDT",
  "vehicle_number": "DH-1234",
  "pump_name": "Shell Dhaka"
}
```

---

## Database Indexes

| Collection | Field(s) | Type |
|------------|----------|------|
| users | email | unique |
| vehicles | vehicle_number | unique |
| pumps | license | unique |
| pump_employees | (pump_id, user_id) | unique compound |
| fuel_prices | fuel_type | index |
| fuel_prices | (fuel_type, effective_from) | unique compound |
| transactions | vehicle_id | index |
| transactions | pump_id | index |
| transactions | created_at | index |
