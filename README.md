# Diversio Engineer I Exercise — HRIS Import Preview Backend

Django backend for the Diversio Engineer I HRIS Import Preview exercise.

The backend accepts an HRIS CSV upload, validates employee identity data, resolves manager relationships, calculates direct-report counts, and identifies employees that belong to reporting cycles. The analysis happens in memory; employee and relationship data are not persisted.

## Tech Stack

- Python
- Django
- Pandas
- django-cors-headers
- pytest

## Project Structure

```text
DiversioBackend/
├── admin_controller/
│   ├── urls.py
│   └── views.py
├── core/
│   └── csv_parser.py
├── diversiobackend/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── tests/
│   └── core_csv_parser_test.py
├── manage.py
├── requirements.txt
└── README.md
```

### Responsibilities

`core/csv_parser.py` contains the CSV parsing, validation, manager-resolution, direct-report counting, and cycle-detection logic.

`admin_controller/views.py` contains the HTTP endpoints and upload-level validation/error handling.

`tests/core_csv_parser_test.py` contains focused tests for identity integrity and reporting-cycle detection.

## Requirements

- Python 3.12+
- pip

Django 6.1 requires a recent supported Python version, so Python 3.12+ is recommended for this project.

## Setup

From the backend directory:

```bash
python -m venv .venv
```

Activate the virtual environment.

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Run the Server

```bash
python manage.py runserver
```

The backend will be available at:

```text
http://127.0.0.1:8000/
```

The React frontend is configured to call this backend.

## API Endpoints

### Health Check

```http
GET /admin/health
```

Example response:

```json
{
  "status": "ok"
}
```

### CSV Import Preview

```http
POST /admin/csv-parser
```

The CSV must be sent as multipart form data using the field name `file`.

A successful response includes:

- `total_rows`
- `accepted_rows`
- `invalid_rows`
- `root_employees`
- `manager_relationships`
- `manager_report_counts`
- `manager_errors`
- `cyclic_employees`

## CSV Contract

The expected headers are:

```csv
employee_id,employee_name,email,manager_id,manager_email,department
```

Headers are expected as a set, so their order does not matter.

Values are normalized as follows:

- Surrounding whitespace is trimmed from every value.
- `email` and `manager_email` are lowercased.
- Employee IDs remain case-sensitive.
- Source row numbers are tracked starting at row 2 because row 1 is the CSV header.

Pandas is used for CSV parsing, including quoted CSV values such as names containing commas.

## Employee Identity Rules

`employee_id` and `email` are required.

Each must be unique after normalization. Every row involved in a duplicate employee ID or duplicate email is treated as invalid and excluded from manager/hierarchy analysis.

Invalid rows are returned with their source row number and validation errors.

## Manager Resolution

Manager fields can be supplied in four ways:

1. Both blank — the employee is a root employee.
2. Only `manager_id` supplied — resolve by employee ID.
3. Only `manager_email` supplied — resolve by normalized email.
4. Both supplied — both references must identify the same employee.

The backend reports errors when:

- the manager cannot be found;
- `manager_id` and `manager_email` identify different employees;
- an employee attempts to manage themselves.

An employee with a manager error remains an accepted employee, but does not create a reporting relationship and is not classified as a root.

## Reporting Cycles

Reporting relationships are represented as employee → manager mappings.

Cycle detection walks each chain while maintaining both a global visited set and the current traversal path. When a previously seen employee is encountered within the current path, the employees belonging to that cycle are marked as cyclic.

## Tests

Run the tests with:

```bash
pytest
```

Current focused tests cover:

- duplicate employee identity handling;
- ensuring invalid identity rows do not create relationships;
- reporting-cycle detection;
- ensuring employees who only report into a cycle are not classified as cyclic.

## Error Handling

The upload endpoint returns clear HTTP errors for common invalid requests, including:

- missing file;
- empty file;
- non-CSV file extension;
- invalid CSV headers;
- CSV parsing/validation errors.

Unexpected processing errors are logged and returned as a generic 500 response instead of exposing an unhandled exception.

## CORS

The development configuration allows the React/Vite frontend origin:

```text
http://localhost:5173
```

This is intended for local development and should be replaced with environment-specific configuration for a production deployment.

## Database

The exercise does not require database persistence. The CSV is analyzed in memory and no employee or reporting relationship records are written as part of the import preview.

The Django project still contains the default SQLite configuration generated by Django.

## Assumptions and Known Limitations

- This is a small exercise application, not a production HRIS ingestion service.
- The current API expects the exact six CSV columns required by the exercise.
- The current implementation uses Pandas and in-memory data structures, so memory usage grows with the size of the uploaded file.
- The cycle-detection approach is designed to avoid repeated traversal of already-explored chains.
- More automated tests could be added for manager lookup by email, conflicting manager references, self-management, root detection, malformed CSV input, and large-file performance.
- Production configuration would move secrets, allowed origins, and API configuration out of source code.

## AI Usage

AI tools were used as development assistance during the exercise. I remained responsible for reviewing, understanding, testing, and validating the resulting code.

- **ChatGPT** and **AI Studio**: Used for suggestions, documentation structure, code analysis and clarifying complex logic patterns


## Time Spent

Approximate implementation time: **~70 - 80** minutes.

## Related Frontend

The browser UI is implemented separately in the `diversiofrontend` project. See that project's README for frontend setup and usage instructions.
