# Office Solution Assessment

Full-stack assessment app that ingests heterogeneous order data from `./data`, normalizes it through a Flask API, and renders a React operations dashboard.

## Project Layout

```text
/backend      Flask API, loaders, services, tests
/frontend     Vite + React + TypeScript dashboard
/data         Provided source data
README.md     Setup and run instructions
DECISIONS.md  Key design decisions and unified schema
NOTES.md      Data inspection and problem-statement notes
```

## Backend Setup

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
py run.py
```

The backend defaults to `http://127.0.0.1:5000`.

`FLASK_DEBUG` is `false` in `.env.example` so the demo runs as a single local process. Set it to `true` only when you specifically want Flask's debug reloader.

## Frontend Setup

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

The frontend defaults to `http://127.0.0.1:5173`.

## Run Locally

Use two terminals:

```powershell
# Terminal 1
cd backend
.\.venv\Scripts\Activate.ps1
py run.py
```

```powershell
# Terminal 2
cd frontend
npm run dev
```

## Tests And Quality

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
ruff check .
black --check .
```

```powershell
cd frontend
npm run lint
npm run build
```

## API Endpoints

### `GET /health`

Returns service and ingestion status.

Example response:

```json
{
  "status": "ok",
  "categories": ["Electronics", "Furniture"],
  "shipment_statuses": ["Delayed", "Delivered"],
  "source_counts": {
    "orders": 2,
    "products": 3,
    "shipments": 2,
    "normalized_orders": 2
  },
  "errors": []
}
```

### `POST /ingest/json`

Reloads `data/Orders.json`.

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:5000/ingest/json
```

### `POST /ingest/csv`

Reloads `data/Products.csv`.

### `POST /ingest/xml`

Reloads `data/Shipment.xml`.

### `POST /ingest/all`

Reloads all source files and recomputes normalized orders.

### `GET /orders`

Returns normalized orders with pagination, filtering, and sorting.

Example:

```text
GET /orders?category=Electronics&page=1&page_size=10&sort_by=total_value&sort_dir=desc
```

Example response:

```json
{
  "data": [
    {
      "order_id": "1001",
      "customer_name": "Rahul",
      "order_date": "2024-01-01",
      "categories": ["Electronics"],
      "total_value": 2200.0,
      "base_currency": "INR",
      "converted_total_value": 26.4,
      "display_currency": "USD",
      "shipment_status": "Delivered",
      "delivery_days": 3,
      "is_delayed": false
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

Supported filters:

- `date_from=YYYY-MM-DD`
- `date_to=YYYY-MM-DD`
- `category=Electronics`
- `status=Delivered`
- `delayed=true`
- `search=Rahul`

Supported sorting:

- `order_id`
- `customer_name`
- `order_date`
- `total_value`
- `delivery_days`
- `shipment_status`

### `GET /orders/<order_id>`

Returns one normalized order with line-item drill-down fields.

### `GET /metadata`

Returns filter options and source counts.

### `GET /analytics/summary`

Returns KPI, trend, category, delivery, currency, and external context data. Accepts the same filters as `/orders`.

Example:

```text
GET /analytics/summary?date_from=2024-01-01&date_to=2024-01-31
```

### `GET /external/currency-context`

Calls the REST Countries API configured in `.env` and summarizes countries that use the configured base currency.

## Assumptions

- Source prices are treated as INR by default because no currency is present in the data.
- Orders are delayed when shipment status says `Delayed` or delivery days exceed `DELAY_THRESHOLD_DAYS`.
- REST Countries is used because it is specified in `Hit External API.xlsx`; a separate exchange-rate API is used for actual currency conversion because REST Countries does not provide rates.
- In-memory storage is sufficient for the sample dataset and keeps the transformation pipeline easy to review.
