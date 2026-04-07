# Fuel Tracking System

A Fuel Tracking System where users can log fuel transactions at specific pumps for their vehicles. It provides a real-time central dashboard that updates instantly using MongoDB Change Streams and Socket.IO. Built with Python Flask for the backend and MongoDB as the database.

## Tech Stack

- **Backend:** Python, Flask
- **Database:** MongoDB (via Flask-PyMongo)
- **Real-time:** Socket.IO (flask-socketio, gevent)
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
SECRET_KEY=your-secret-key
```

### 4. Run migrations

```bash
python migrate.py upgrade
```

### 5. Run the server

```bash
python run.py
```

Server runs at `http://localhost:5000`
Dashboard at `http://localhost:5000/dashboard`

### 6. Run tests

```bash
venv\Scripts\python -m pytest tests/ -v
```

---

## Roles

| Role | Description |
|------|-------------|
| User | Registers vehicles, records fuel entries |
| Admin | Manages pumps, fuel prices |

---

## Schema

### User
| Field | Type | Description |
|-------|------|-------------|
| _id | string (uuid) | Primary key |
| name | string | Full name |
| license | string | Unique license number |
| created_at | datetime | Creation timestamp |

### Vehicle
| Field | Type | Description |
|-------|------|-------------|
| _id | string (uuid) | Primary key |
| user_id | string | FK → User |
| vehicle_number | string | Unique plate number |
| type | string | Vehicle type (car, truck, etc.) |
| created_at | datetime | Creation timestamp |

### Pump
| Field | Type | Description |
|-------|------|-------------|
| _id | string (uuid) | Primary key |
| name | string | Station name |
| location | string | Station location |
| license | string | Unique pump license |
| created_at | datetime | Creation timestamp |

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

> `fuel_type`, `unit`, and `currency` are not stored on Transaction — they are accessed via `fuel_price_id` join.

---

## Relations

```
User       ──< Vehicle
Vehicle    ──< Transaction
Pump       ──< Transaction
FuelPrice  ──< Transaction
```

---

## API Reference

All responses follow this structure:

```json
// Success
{ "status": 200, "message": "...", "data": { ... } }

// Created
{ "status": 201, "message": "...", "data": { ... } }

// Paginated
{
  "status": 200,
  "message": "...",
  "data": {
    "<key>": [...],
    "pagination": { "page": 1, "limit": 10, "total": 50, "total_pages": 5 }
  }
}

// Error
{ "status": 4xx, "message": "...", "errors": { ... } }
```

---

### Users

#### `POST /api/users/`
Create a new user.

**Request body:**
```json
{ "name": "John Doe", "license": "DL-12345" }
```

**Responses:** `201 Created` / `400 Validation failed` / `409 License already exists`

---

#### `GET /api/users/`
Get all users (paginated).

**Query params:** `?page=1&limit=10`

**Response:** `200` with `users[]` + pagination

---

#### `GET /api/users/<user_id>`
Get a single user by ID.

**Responses:** `200` / `404 User not found`

---

### Vehicles

#### `POST /api/vehicles/`
Create a new vehicle.

**Request body:**
```json
{ "user_id": "...", "vehicle_number": "DH-1234", "vehicle_type": "car" }
```

**Responses:** `201` / `400` / `404 User not found` / `409 Vehicle number already exists`

---

#### `GET /api/vehicles/`
Get all vehicles (paginated).

**Query params:** `?page=1&limit=10`

---

#### `GET /api/vehicles/<vehicle_id>`
Get a single vehicle by ID.

**Responses:** `200` / `404`

---

#### `GET /api/vehicles/user/<user_id>`
Get all vehicles for a user (paginated).

**Responses:** `200` / `404 User not found`

---

### Pumps

#### `POST /api/pumps/`
Create a new pump.

**Request body:**
```json
{ "name": "Shell Dhaka", "location": "Mirpur", "license": "P-001" }
```

**Responses:** `201` / `400` / `409 License already exists`

---

#### `GET /api/pumps/`
Get all pumps (paginated).

---

#### `GET /api/pumps/<pump_id>`
Get a single pump by ID.

**Responses:** `200` / `404`

---

### Fuel Prices

#### `POST /api/fuel-prices/`
Create a new fuel price entry.

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

> `currency` is optional — defaults to `BDT`.

**Responses:** `201` / `400`

---

#### `GET /api/fuel-prices/`
Get all fuel prices (paginated).

---

#### `GET /api/fuel-prices/<fuel_price_id>`
Get a single fuel price by ID.

**Responses:** `200` / `404`

---

#### `GET /api/fuel-prices/latest/<fuel_type>`
Get the latest active price for a fuel type.

**Example:** `GET /api/fuel-prices/latest/octane`

**Responses:** `200` / `404 No fuel price found`

---

### Transactions

#### `POST /api/transactions/`
Record a fuel transaction.

**Request body:**
```json
{
  "vehicle_id": "...",
  "pump_id": "...",
  "fuel_type": "octane",
  "quantity": 10.0
}
```

> `total_price` is calculated automatically: `quantity × latest price_per_unit`

**Responses:** `201` / `400` / `404 Vehicle/Pump/FuelPrice not found`

---

#### `GET /api/transactions/`
Get all transactions (paginated).

---

#### `GET /api/transactions/<transaction_id>`
Get a single transaction by ID.

**Responses:** `200` / `404`

---

#### `GET /api/transactions/vehicle/<vehicle_id>`
Get all transactions for a vehicle (paginated).

**Responses:** `200` / `404 Vehicle not found`

---

#### `GET /api/transactions/pump/<pump_id>`
Get all transactions for a pump (paginated).

**Responses:** `200` / `404 Pump not found`

---

## Real-time (Socket.IO)

Connect to namespace `/dashboard`.

### Events received from server

| Event | Payload | Description |
|-------|---------|-------------|
| `init` | `{ stats, transactions[] }` | Sent on connect — initial dashboard data |
| `new_transaction` | transaction object | Broadcast when a new transaction is created |
| `stats_update` | stats object | Broadcast when dashboard stats change |

### Stats object
```json
{
  "total_transactions": 120,
  "total_fuel": 1500.5,
  "total_revenue": 187562.5
}
```

---

## Database Indexes

| Collection | Field | Type |
|------------|-------|------|
| users | license | unique |
| vehicles | vehicle_number | unique |
| vehicles | user_id | index |
| pumps | license | unique |
| fuel_prices | fuel_type | index |
| transactions | vehicle_id | index |
| transactions | pump_id | index |
| transactions | created_at | index |
