# Engineering Decisions

## Frontend Tooling

The frontend uses Vite with React and TypeScript. Vite is faster and lighter than Create React App for this assessment, has a straightforward dev server, and keeps the project structure easy to review.

The Vite build splits React, charting, and icon dependencies into explicit chunks. Recharts is the only heavy dependency, so the warning limit is set to `650 KB` for that isolated vendor chart chunk while keeping app code and icons in smaller cacheable assets.

## Storage

The backend uses an in-memory repository. The source dataset is very small, the exercise emphasizes transformation logic, and the problem statement explicitly allows in-memory storage. The repository is still isolated behind service classes so it can be replaced with SQLite or PostgreSQL without rewriting route handlers.

## Unified Internal Schema

The normalized API works with order-level records shaped as:

```json
{
  "order_id": "1001",
  "customer_id": "C001",
  "customer_name": "Rahul",
  "order_date": "2024-01-01",
  "items": [
    {
      "product_id": "P101",
      "product_name": "Laptop",
      "category": "Electronics",
      "quantity": 2,
      "unit_price": 500.0,
      "line_total": 1000.0
    }
  ],
  "item_count": 3,
  "categories": ["Electronics"],
  "total_value": 2200.0,
  "base_currency": "INR",
  "converted_total_value": 26.4,
  "display_currency": "USD",
  "shipment": {
    "shipment_id": "S001",
    "delivery_days": 3,
    "status": "Delivered"
  },
  "shipment_status": "Delivered",
  "delivery_days": 3,
  "is_delayed": false
}
```

This keeps nested line items available for drill-down while exposing denormalized order fields for filtering, sorting, charting, and table display.

## Data Cleanup

`Orders.json` and `Products.csv` contain a UTF-8 BOM and line-level quote artifacts. The loaders perform conservative cleanup before parsing:

- JSON loader first tries strict parsing, then unwraps CSV-style quoted lines and retries.
- CSV loader unwraps rows that are quoted as a whole record before passing them to `csv.DictReader`.

The original files are not modified.

## Delay Rule

An order is delayed when its shipment status contains `Delayed` or when `delivery_days` exceeds the configurable `DELAY_THRESHOLD_DAYS` value. The default threshold is `5` days. This combines explicit source status with a numeric fallback for inconsistent shipment data.

## Currency And External APIs

Source prices do not include a currency. The app assumes INR by default, configurable with `BASE_CURRENCY`.

The spreadsheet specifically names REST Countries API, so the backend uses it for currency/country context. Because REST Countries is not an exchange-rate API, the backend also uses a configurable no-key exchange-rate endpoint for conversion:

- `REST_COUNTRIES_URL=https://api.restcountries.com/countries/v5/currencies?q={currency}&response_fields=names.common,codes.alpha_2,region,population,area,currencies&limit=100`
- `REST_COUNTRIES_ALL_URL=https://api.restcountries.com/countries/v5?response_fields=names.common,codes.alpha_2,region,population,area,currencies&limit={limit}&offset={offset}`
- `REST_COUNTRIES_API_KEY` is read from `backend/.env` and sent as a bearer token.
- `EXCHANGE_RATE_URL=https://open.er-api.com/v6/latest`

Both clients have short timeouts and fallback responses so dashboard data still loads when the network or public APIs are unavailable.

The external relationship dashboard normalizes nested REST Countries records into country-currency rows. Countries with multiple currencies intentionally produce multiple rows because the relationship being explored is country -> currency -> population, not just country metadata.

Fallback responses intentionally expose concise user-safe messages rather than raw exception text. This prevents local proxy, DNS, timeout, or public API errors from leaking implementation details into the dashboard while still making the fallback status explicit.

## Local Runtime

`FLASK_DEBUG` defaults to `false` for `backend/run.py` and `.env.example` so the local launcher uses a single Flask process. Developers can set `FLASK_DEBUG=true` while actively debugging, but the assessment demo avoids the debug reloader because stale workers can keep old API responses alive on port `5000`.

The backend loads an optional project-root `.env` first and then `backend/.env` with override enabled. This matches the README setup while still allowing repo-level defaults if the app is embedded into a larger environment.

External API calls use a `requests.Session` with `trust_env` controlled by `EXTERNAL_API_TRUST_ENV_PROXY`, defaulting to `false`. This avoids a common local assessment failure where inherited proxy variables point HTTPS traffic at an unavailable localhost proxy.

## API Shape

The DOCX requires `/ingest/json`, `/ingest/xml`, `/ingest/csv`, and `/analytics/summary`, so those exact paths are implemented. Additional resource-oriented endpoints are provided for the frontend:

- `GET /orders`
- `GET /orders/<order_id>`
- `GET /metadata`
- `GET /external/currency-context`
- `GET /health`

List endpoints use query-string filters, pagination, and sorting rather than custom RPC-style request bodies.

## Frontend State

The React app uses Context plus hooks for dashboard state because the state graph is small: filters, sort, pagination, selected row, and loaded API data. Redux or Zustand would be reasonable if multiple independent pages started sharing cache invalidation rules, optimistic updates, or complex cross-page workflows.
