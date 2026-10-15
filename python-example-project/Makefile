# Test commands. Each target is one plain command; run it directly if you
# prefer (or are on Windows without make).

.PHONY: run test test-unit test-integration test-e2e test-all coverage coverage-unit coverage-integration coverage-summary docker-build smoke

run:
	python -m app

test:                    ## unit + integration (fast, no browser needed)
	pytest

test-unit:
	pytest tests/unit

test-integration:
	pytest tests/integration

test-e2e:                ## real browser, real server
	pytest tests/e2e --screenshot only-on-failure

test-all: test test-e2e

coverage:                ## unit + integration with a coverage table, HTML in htmlcov/, JSON in coverage.json
	pytest --cov --cov-report=term-missing --cov-report=html --cov-report=json

coverage-unit:
	pytest tests/unit --cov --cov-report=term-missing

coverage-integration:
	pytest tests/integration --cov --cov-report=term-missing

coverage-summary:        ## reprint the last `make coverage` run as a Markdown table with raw counts
	python scripts/coverage_summary.py

docker-build:            ## build the same image CI builds
	docker build -t python-example-project .

smoke:                   ## smoke-test a running server (start it first: `make run` or `docker run`)
	python scripts/smoke_test.py
