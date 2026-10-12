# Retail Spending Insights

A full-stack portfolio project that turns synthetic retail transactions into weekly spending metrics. A React/TypeScript dashboard lets users select a merchant and explore spending, purchases, and customer activity calculated by a FastAPI backend and PostgreSQL.

The project practices an alternative-data workflow: validate raw records, import them safely, calculate useful metrics, and expose results through an API and dashboard.

## Features

- Validate CSV headers, required identifiers, dates, and monetary values.
- Separate accepted records from rejected rows with rejection reasons.
- Detect duplicate IDs within a CSV and skip existing IDs during database imports.
- Import in batches within one database transaction, with rollback on database failures.
- Retrieve an alphabetical merchant list and weekly metrics through FastAPI.
- Filter metrics by inclusive start and end dates through the API.
- View metrics in a React/TypeScript table with a merchant dropdown, loading states, and error messages.
- Cancel stale frontend requests when changing merchants.

## Technology

| Layer | Tools |
| --- | --- |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL, psycopg |
| Frontend | React, TypeScript, Vite |
| Data processing | Python csv, datetime, and Decimal |

## Sample data

`data/synthetic_retail_transactions.csv` contains 5,000 synthetic purchases across July–September 2026 for Amazon, Walmart, and Target. Customer IDs are fictional. There are no card numbers or personal details, and records do not represent actual retailer performance.

```csv
transaction_id,customer_id,merchant_name,transaction_date,amount
TX000208,C0306,Amazon,2026-07-01,235.52
```

Amounts are interpreted as USD. The supplied dataset has no refunds or intentionally invalid rows, though the code supports negative refund amounts and row rejection.

## Project structure

```text
retail-spending-insights/
├── BackEnd/
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── main.py
│   ├── init_db.py
│   ├── preview_data.py
│   ├── import_transactions.py
│   ├── services/
│   │   ├── transactions.py
│   │   └── metrics.py
│   └── tests/
├── FrontEnd/
│   ├── package.json
│   └── src/
│       ├── App.tsx
│       ├── App.css
│       ├── index.css
│       ├── services/api.ts
│       └── types/metrics.ts
├── data/synthetic_retail_transactions.csv
├── requirements.txt
├── .gitignore
└── README.md
```

## Local setup

Install PostgreSQL, Conda, and a Node.js version supported by your installed Vite version. Ensure PostgreSQL is running.

### 1. Clone and install Python dependencies

```bash
git clone https://github.com/timkorpal/retail-spending-insights.git
cd retail-spending-insights
conda create -n retail_insights python=3.12 -y
conda activate retail_insights
python -m pip install -r requirements.txt
```

### 2. Create the database

On Ubuntu, open the PostgreSQL administrative console:

```bash
sudo -u postgres psql
```

Run inside psql:

```sql
CREATE USER retail_user;
\password retail_user
CREATE DATABASE retail_insights_db OWNER retail_user;
\q
```

The password command prompts for a password. Create `BackEnd/.env` with your local settings:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=retail_insights_db
DB_USER=retail_user
DB_PASSWORD=your_local_password
```

Keep this file out of Git. Never commit database passwords.

### 3. Initialize and import

From the project root:

```bash
python BackEnd/init_db.py
python BackEnd/preview_data.py
python BackEnd/import_transactions.py
```

For an empty database, the importer reports 5,000 inserted records. Running it again reports zero inserted and 5,000 already stored. The unique database constraint protects against duplicate transaction IDs.

`init_db.py` creates missing tables; it does not migrate existing schemas. Alembic is included in dependencies but migrations are not yet configured.

### 4. Start FastAPI

```bash
cd BackEnd
uvicorn main:app --reload
```

API documentation: http://127.0.0.1:8000/docs

### 5. Start the frontend

Open another terminal and run from the project root:

```bash
cd FrontEnd
npm ci
npm run dev
```

Open the URL printed by Vite. Backend CORS allows `http://localhost:5173` and `http://127.0.0.1:5173`. If Vite uses a different port, update the allowed origins or free port 5173.

The frontend currently calls `http://127.0.0.1:8000` and retrieves all available weeks for the selected merchant.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/merchants` | Distinct merchant names |
| GET | `/merchants/{merchant_name}/weekly-metrics` | Weekly metrics with optional `start_date` and `end_date` |

```bash
curl http://127.0.0.1:8000/merchants
curl 'http://127.0.0.1:8000/merchants/Amazon/weekly-metrics?start_date=2026-07-01&end_date=2026-07-31'
```

Unknown merchants return 404. Invalid dates or a start date after the end date return 422. A known merchant with no transactions in the requested range returns an empty list.

## Metric definitions

| Metric | Definition |
| --- | --- |
| Week start | Monday of the transaction's calendar week |
| Gross purchase spending | Sum of positive amounts |
| Refund amount | Absolute value of the sum of negative amounts |
| Net observed spending | Sum of all transaction amounts |
| Purchase count | Count of positive transactions |
| Unique purchasing customers | Distinct customers with a positive transaction that week |
| Average purchase amount | Average positive amount, rounded to cents; null when there are no purchases |

Money is stored as PostgreSQL NUMERIC and processed as Python Decimal. The API returns decimal values as JSON strings; the frontend converts them to numbers only for display formatting.

## Validation and limitations

The implementation has been manually exercised by previewing 5,000 accepted rows, importing them, retrieving weekly API responses, and displaying metrics in the frontend. Automated tests are a planned addition.

Build the frontend from `FrontEnd`:

```bash
npm run build
```

- Observed spending in a sample is not total company revenue.
- Weeks at dataset or filter boundaries may be partial. July 1 belongs to the week starting June 29.
- Missing weeks are omitted, not filled with zero. Data completeness is not yet monitored.
- Unique customer counts are calculated per week; adding them across weeks double-counts returning customers.
- Reimporting an existing transaction ID skips it, even if its values have changed. Corrections need a separate policy.
- Merchant names are currently used as supplied; normalization is not implemented.
- Imports are local CLI operations. There is no upload endpoint, persistent import audit, or authentication yet.

## Planned improvements

- Frontend date filters and spending trend charts.
- Merchant alias normalization and review of unknown names.
- Persistent import history and rejected-row records.
- Explicit source coverage tracking and partial-week indicators.
- Tests for validation, aggregation, duplicate imports, and rollback.
- Database migrations and deployment configuration.
