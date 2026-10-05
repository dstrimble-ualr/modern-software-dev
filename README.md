# python-example-project

A small Flask app with cookie-based login and a widgets page, built for teaching
automated testing in Python. It is the Python twin of `dstrimble-example-project`
(Node.js): same front end, same API, same three test layers.

## Tech stack

- Python 3.12 or newer
- Flask
- SQLite (standard library) for the database
- pytest, pytest-cov (unit and integration tests, coverage)
- Playwright for Python via pytest-playwright (end-to-end tests)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium        # one-time browser download for the E2E tests
```

## Run the app

```bash
python -m app                      # http://localhost:8000, login admin / password
```

The database is a SQLite file, `app.db` by default. Set `APP_DB_PATH` to change it.
Set `DEFAULT_ADMIN_PASSWORD` to change the seeded admin password.

## Testing

Three layers, three folders, three commands:

| Layer | Folder | Command | What is real | What is faked |
|---|---|---|---|---|
| Unit | `tests/unit/` | `make test-unit` | One module of pure functions | Everything else is absent |
| Integration | `tests/integration/` | `make test-integration` | The Flask app, routes, cookies, real SQL on in-memory SQLite | Nothing, but the DB is in memory |
| End-to-end | `tests/e2e/` | `make test-e2e` | A real Chromium browser and the real server process | Nothing |

- `make test` (or plain `pytest`) runs unit + integration. Fast, no browser needed.
- `make test-all` runs everything.
- `make coverage` runs the fast layers with a coverage table, plus an HTML report in `htmlcov/index.html`.
- `make coverage-unit` and `make coverage-integration` show what each layer covers on its own.
- `make coverage-summary` reprints the last coverage run as a table with raw covered/total counts.

Every `make` target is a single plain command. Open the `Makefile` to see it, or run
the command directly if you do not have `make`.

See [TESTING_PLAYBOOK.md](TESTING_PLAYBOOK.md) for the class walkthrough: it explains
what each layer proves and includes verified break/fix demos.

## Docker

```bash
docker build -t python-example-project .
docker run --rm -p 8000:8000 python-example-project
```

## Security notes

This example stores passwords in plaintext and uses a fixed token as the login cookie.
That keeps the code short for teaching. Do not copy either idea into a real application.
