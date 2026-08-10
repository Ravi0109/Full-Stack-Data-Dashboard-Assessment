# Data and Problem Notes

## Inspected Files

The `./data` directory contains five source files:

- `Excercise.docx` (249,282 bytes): problem statement plus dashboard reference images.
- `Hit External API.xlsx` (9,787 bytes): external API reference.
- `Orders.json` (604 bytes): order source data.
- `Products.csv` (112 bytes): product catalog source data.
- `Shipment.xml` (360 bytes): shipment source data.

## Problem Statement Summary

The Word document asks for a full-stack exercise with a Flask backend and React frontend. The backend should expose ingestion endpoints for each data format:

- `/ingest/json` to load JSON order data.
- `/ingest/xml` to load XML shipment data.
- `/ingest/csv` to load CSV product data.
- `/analytics/summary` to return aggregate metrics.

Core data-processing expectations:

- Flatten nested JSON orders and items.
- Parse XML properly.
- Join orders, shipments, and products.
- Handle missing values, data inconsistencies, and type conversions.
- Derive total order value.
- Derive a delivery delay flag.
- Produce category-level aggregation.
- Include currency conversion using an API.

Storage is intentionally open-ended. The document says candidates may choose in-memory storage, pandas, SQLite, or PostgreSQL, and that the decision should be justified.

Frontend expectations:

- Dashboard page.
- KPI cards for total orders, total revenue, and delayed orders.
- Charts for revenue trend, category-wise revenue, and delivery performance.
- Filters for date range, category, and delivery status.
- Dynamic API fetching with loading and error states.
- Advanced UI features such as view toggles, drill-down, reusable components, and responsive design.
- State management with Redux or Context.

The embedded DOCX images are dashboard UI examples only; they do not add extra data fields or hidden business rules beyond the extracted text.

## External API Reference

`Hit External API.xlsx` contains a single worksheet describing the REST Countries API:

- Website: REST Countries API.
- Example endpoint: `https://restcountries.com/v3.1/all`.
- Notes: deeply nested JSON, no API key required, useful for transformations and relational modeling.
- Suggested exercise ideas: extract country, currency, and population relationships; normalize nested JSON; build filters by region and population range; compare population-density-like metrics.

Because the core exercise also asks for currency conversion, the application will use the spreadsheet-mentioned REST Countries API for currency metadata/context and a separate configurable exchange-rate API for the actual conversion rate. Both calls must fail gracefully.

## Source Data Shape

### `Orders.json`

The file is intended to be JSON with this logical shape:

```json
{
  "orders": [
    {
      "order_id": "1001",
      "customer": { "id": "C001", "name": "Rahul" },
      "items": [
        { "product_id": "P101", "qty": 2, "price": 500 },
        { "product_id": "P102", "qty": 1, "price": 1200 }
      ],
      "order_date": "2024-01-01"
    }
  ]
}
```

Actual file note: it includes a UTF-8 BOM and extra quote escaping around several lines, so a resilient loader is required before JSON parsing. There are two logical orders:

- Order `1001`, customer `C001` / `Rahul`, date `2024-01-01`, items `P101 x2 @ 500` and `P102 x1 @ 1200`.
- Order `1002`, customer `C002` / `Anita`, date `2024-01-02`, item `P103 x3 @ 200`.

### `Products.csv`

The file is intended to be CSV with columns:

- `ProductID`
- `ProductName`
- `Category`

Actual file note: it includes a UTF-8 BOM and each whole row is wrapped in quotes, so the CSV loader should unwrap rows before parsing.

Logical rows:

| ProductID | ProductName | Category |
| --- | --- | --- |
| P101 | Laptop | Electronics |
| P102 | Phone | Electronics |
| P103 | Chair | Furniture |

### `Shipment.xml`

The XML root is `<shipments>` with repeated `<shipment>` children.

Each shipment has:

- `shipment_id`
- `order_id`
- `delivery_days`
- `status`

Logical rows:

| shipment_id | order_id | delivery_days | status |
| --- | --- | ---: | --- |
| S001 | 1001 | 3 | Delivered |
| S002 | 1002 | 7 | Delayed |

## Data Quality Observations

- Orders and products require cleanup before standard parsing because of extra quotation artifacts.
- Product IDs join order items to products.
- Order IDs join orders to shipments.
- Shipment status already marks delayed shipments, but a numeric delay flag can also be derived from delivery days.
- Source prices have no explicit currency. The app will treat them as INR by default because the sample customer names and exercise context suggest India, and this will be configurable.
