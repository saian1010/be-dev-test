# Backend Developer Test Solution

This repository is a small customer directory application built around a CSV import, a lightweight HTTP API, and a browser UI.

The workflow is:

1. Import `data/customers.csv` into SQLite.
2. Serve customer data through JSON endpoints.
3. Render a searchable, paginated list and a detail page in the browser.

## What It Does

- Imports customer records from CSV into SQLite.
- Exposes a paginated list endpoint with search.
- Exposes a customer detail endpoint.
- Serves a list page for browsing records.
- Serves a detail page for viewing one customer.
- Lets you open or copy a customer's website URL from the detail page.

## Project Layout

```text
customer_directory/
  api/
    common.py
    customers.py
  config/
    config.py
  db/
    database.py
  static/
    pages/
      index.html
      customer.html
    resources/
      app.css
      app.js
      customer.js
    vendor/
      bootstrap.min.css
      jquery.min.js
      pagination.css
      pagination.min.js
  utils/
    import_csv.py
  server.py
  import_csv.py
  database.py
data/
var/
tests/
```

## Run It

Requirements:

- Python 3.11+

No Python package installation is required for the backend.

Import the dataset:

```bash
python3 -m customer_directory.import_csv
```

Start the server:

```bash
python3 -m customer_directory.server
```

Open the app:

```text
http://127.0.0.1:8000
```

## API

### `GET /health`

Returns a simple health check response.

### `GET /api/customers?page=1&page_size=20&search=laura`

Returns a paginated list of customers.

Query parameters:

- `page`: page number, must be `>= 1`
- `page_size`: page size, must be between `1` and `100`
- `search`: optional free-text search across multiple fields

Search is applied across:

- `first_name`
- `last_name`
- `email`
- `gender`
- `company`
- `city`
- `title`

### `GET /api/customers/{id}`

Returns a single customer record with all fields.

## UI

### List page

- Displays name, email, gender, company, city, and title.
- Supports text search across the list.
- Uses remote pagination.
- Opens the detail page when a customer name is clicked.

### Detail page

- Shows the full customer record.
- Uses a cleaner card-based layout with a more compact summary section.
- Shows a shortened `website` value with a copy button next to it.

## Validation

- Invalid `page` and `page_size` values return `400 Bad Request`.
- Missing customer records return `404 Not Found`.
- The import command recreates the schema if needed and reloads the dataset.

## Data Storage

- Source data: `data/customers.csv`
- SQLite database: `var/customers.db`

The database file is generated locally and is not meant to be committed.

## Tests

Run the test suite with:

```bash
python3 -m unittest discover -s tests -v
```

## Why These Technologies

### Python standard library

The backend uses the Python standard library instead of a framework to keep the solution small and explicit. For a coding exercise, that reduces setup noise and makes the request/response flow easier to review.

### SQLite

SQLite is a good fit for a fixed dataset of 1,000 rows. It keeps persistence simple, avoids external services, and still gives us structured queries, filtering, and pagination.

### WSGI via `wsgiref`

The server is built on the standard WSGI entry point so the HTTP layer stays lightweight and dependency-free. That is enough for a small internal-style application and keeps the code easy to run anywhere Python is available.

### Plain HTML, CSS, and JavaScript

The UI is intentionally simple. There is no frontend build step, no framework runtime, and no bundler. That makes the app fast to start and easy to inspect.

### Bootstrap CSS

Bootstrap provides a clean base layout and form/table styling without needing to write a large custom stylesheet. I used a small amount of local CSS only where the default utilities were not enough.

### jQuery and Pagination.js

The pagination control needs client-side page rendering and a "go to page" input. Using a small, vendored pagination plugin avoids rewriting pagination behavior by hand while keeping the browser code straightforward.

### Local vendoring for frontend assets

The CSS and JS assets are checked into the repository under `static/vendor/` so the app does not depend on a CDN or external network access at runtime.

### One-click website copy

The detail page shortens the `website` value for readability and keeps a copy action next to it so a user can quickly reuse the URL without selecting text manually.

## Tradeoffs

- This is intentionally not a framework-heavy implementation.
- The backend is simpler to audit, but it would not be the first choice for a larger production system.
- A production version would likely use a web framework, migrations, a richer test suite, and stronger frontend structure.
