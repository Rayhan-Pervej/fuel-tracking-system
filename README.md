# Fuel Tracking System

A Fuel Tracking System where users can log fuel transactions at specific pumps for their vehicles. It provides a real-time central dashboard that updates instantly using MongoDB Change Streams and Socket.IO. Built with Python Flask for the backend and MongoDB as the database.

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

---

## Roles

| Role | Scope | Description |
|------|-------|-------------|
| `admin` | Global | Full access — create pumps, users, fuel prices, view all data |
| `employee` | Global | Can record transactions |
| `customer` | Global | Can register vehicles, self-register |
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
| role | string | `admin`, `employee`, `customer` |
| license | string | License number |
| refresh_token | string | Active refresh token (never returned in responses) |
| refresh_token_expires_at | datetime | Refresh token expiry (never returned in responses) |
| created_at | datetime | Creation timestamp |

### Vehicle
| Field | Type | Description |
|-------|------|-------------|
| _id | string (uuid) | Primary key |
| user_id | string | FK → User |
| vehicle_number | string | Unique plate number |
| vehicle_type | string | `car`, `truck`, `bike`, `bus` |
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
| quantity | float | Amount of fuel (in FuelPrice unit) |
| total_price | float | quantity × price_per_unit (snapshot) |
| created_at | datetime | Creation timestamp |

> `fuel_type`, `unit`, and `currency` are not stored on Transaction — accessed via `fuel_price_id` join.

---

## Relations

```
User            ──< Vehicle
User            ──< PumpEmployee
Vehicle         ──< Transaction
Pump            ──< Transaction
Pump            ──< PumpEmployee
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

#### `POST /api/auth/register`
Self-register as a customer.

**Auth required:** No

**Request body:**
```json
{ "name": "John Doe", "email": "user@example.com", "password": "secret123", "license": "DH-1234" }
```

**Validation:**
- `name`: required, 2–100 characters
- `email`: required, valid email format
- `password`: required, minimum 8 characters
- `license`: required, 3–10 characters

> Role is always `customer` — admin/employee accounts must be created via `POST /api/users/`.

**Responses:** `201` / `400` / `403 Cannot self-register as admin or employee` / `409 Email already exists`

---

### Users

#### `POST /api/users/`
Create a new user (admin or employee).

**Auth required:** `admin`

**Request body:**
```json
{ "name": "John Doe", "email": "user@example.com", "password": "secret123", "role": "employee", "license": "DH-1234" }
```

**Validation:**
- `name`: required, 2–100 characters
- `email`: required, valid email format
- `password`: required, minimum 8 characters
- `role`: optional, defaults to `customer` — one of `admin`, `employee`, `customer`
- `license`: required, 3–10 characters

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
| `role` | string | No | Filter by role: `admin`, `employee`, `customer` |

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

**Responses:** `200` / `401` / `404`

---

#### `PATCH /api/users/<user_id>`
Update a user.

**Auth required:** `admin`

**Request body:** Any subset of `name`, `license`, `role`

**Validation:**
- `name`: 2–100 characters
- `license`: 3–10 characters
- `role`: one of `admin`, `employee`, `customer`

**Responses:** `200` / `400` / `401` / `403` / `404`

---

#### `DELETE /api/users/<user_id>`
Delete a user and cascade-delete their vehicles and pump assignments.

**Auth required:** `admin`

**Responses:** `200` / `401` / `403` / `404`

---

### Vehicles

#### `POST /api/vehicles/`
Create a new vehicle.

**Auth required:** Any authenticated user

> Non-admin users can only create vehicles for themselves (`user_id` must match their own ID).

**Request body:**
```json
{ "user_id": "...", "vehicle_number": "DH-1234", "vehicle_type": "car" }
```

**Responses:** `201` / `400` / `401` / `403` / `404 User not found` / `409 Vehicle number already exists`

---

#### `GET /api/vehicles/`
Get all vehicles (paginated).

**Auth required:** `admin`

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Page size (default: 10, max: 100) |
| `cursor` | string | No | Opaque cursor from previous response |
| `user_id` | string | No | Filter by owner user ID |
| `type` | string | No | Filter by vehicle type: `car`, `truck`, `bike`, `bus` |

**Responses:** `200` / `400` / `401` / `403`

---

#### `GET /api/vehicles/<vehicle_id>`
Get a single vehicle by ID.

**Auth required:** Any authenticated user

> Non-admin users can only view their own vehicles.

**Responses:** `200` / `401` / `403` / `404`

---

#### `GET /api/vehicles/user/<user_id>`
Get all vehicles for a user (paginated).

**Auth required:** Any authenticated user

> Non-admin users can only view vehicles for their own user ID.

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Page size (default: 10, max: 100) |
| `cursor` | string | No | Opaque cursor from previous response |

**Responses:** `200` / `400` / `401` / `403` / `404 User not found`

---

#### `PATCH /api/vehicles/<vehicle_id>`
Update a vehicle.

**Auth required:** Any authenticated user (admin or the vehicle's owner)

**Request body:** Any subset of `vehicle_number`, `vehicle_type`

**Responses:** `200` / `400` / `401` / `403` / `404`

---

#### `DELETE /api/vehicles/<vehicle_id>`
Delete a vehicle.

**Auth required:** Any authenticated user (admin or the vehicle's owner)

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
| `location` | string | No | Filter by location (exact match) |

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

#### `GET /api/pumps/me/pumps`
Get all pump assignments for the currently authenticated user.

**Auth required:** Any authenticated user

**Responses:** `200` / `401`

---

#### `POST /api/pumps/<pump_id>/employees`
Add an employee to a pump.

**Auth required:** Global `admin` OR `pump_admin` of this pump

**Request body:**
```json
{ "email": "employee@example.com", "role": "employee" }
```

> `role` must be `pump_admin` or `employee`. Only one `pump_admin` allowed per pump.
> The user being added must have global role `employee`.

**Responses:** `201` / `400` / `401` / `403` / `404` / `409 Already assigned`

---

#### `DELETE /api/pumps/<pump_id>/employees/<user_id>`
Remove an employee from a pump.

**Auth required:** Global `admin` OR `pump_admin` of this pump

> Cannot remove the `pump_admin` — reassign their role first.

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

**Auth required:** `admin` or `employee`

**Request body:**
```json
{
  "vehicle_id": "...",
  "pump_id": "...",
  "fuel_type": "octane",
  "quantity": 10.0
}
```

**Validation:**
- `vehicle_id`: required
- `pump_id`: required
- `fuel_type`: required, one of `octane`, `diesel`, `petrol`
- `quantity`: required, minimum `0.1`

> `total_price` is calculated automatically: `quantity × latest price_per_unit`. Uses a MongoDB transaction for atomicity.

**Responses:** `201` / `400` / `401` / `403` / `404 Vehicle/Pump/FuelPrice not found`

---

#### `GET /api/transactions/`
Get all transactions (paginated).

**Auth required:** `admin`

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Page size (default: 10, max: 100) |
| `cursor` | string | No | Opaque cursor from previous response |
| `vehicle_id` | string | No | Filter by vehicle ID |
| `pump_id` | string | No | Filter by pump ID |
| `from` | string | No | Start date filter `YYYY-MM-DD` (requires `to`) |
| `to` | string | No | End date filter `YYYY-MM-DD` (requires `from`) |

**Responses:** `200` / `400` / `401` / `403`

---

#### `GET /api/transactions/<transaction_id>`
Get a single transaction by ID.

**Auth required:** Any authenticated user

**Responses:** `200` / `401` / `404`

---

#### `GET /api/transactions/vehicle/<vehicle_id>`
Get all transactions for a vehicle (paginated).

**Auth required:** Any authenticated user

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Page size (default: 10, max: 100) |
| `cursor` | string | No | Opaque cursor from previous response |

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

**Responses:** `200` / `400` / `401` / `404 Pump not found`

---

## Real-time (Socket.IO)

Connect to namespace `/dashboard`. A valid access token **must** be passed in the `auth` object on connect, otherwise the connection will be rejected.

```javascript
const socket = io('http://localhost:5000/dashboard', {
  auth: { token: '<access_token>' }
});
```

### Events received from server

| Event | Payload | Description |
|-------|---------|-------------|
| `init` | `{ stats, transactions[] }` | Sent on connect — last 20 transactions + current stats |
| `new_transaction` | `{ transaction, stats }` | Broadcast when a new transaction is created |

### Stats object
```json
{
  "total_transactions": 120,
  "total_fuel_dispensed": 1500.5,
  "total_revenue": 187562.5
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
| vehicles | user_id | index |
| pumps | license | unique |
| pump_employees | (pump_id, user_id) | unique compound |
| fuel_prices | fuel_type | index |
| fuel_prices | (fuel_type, effective_from) | unique compound |
| transactions | vehicle_id | index |
| transactions | pump_id | index |
| transactions | created_at | index |
