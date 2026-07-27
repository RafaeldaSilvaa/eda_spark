.PHONY: test-all test-unit test-integration test-coverage \
        docker-test docker-shell docker-jupyter docker-benchmark docker-build \
        build shell clean

# ─── Variables ────────────────────────────────────────────────────────
PYTEST   ?= pytest
PACKAGE  ?= spark_eda
SRC_DIR  ?= src/$(PACKAGE)
TEST_DIR ?= tests
BENCH_DIR?= bench_results
COMPOSE  ?= docker compose

# ─── Default ──────────────────────────────────────────────────────────
.DEFAULT_GOAL := test-all

# ─── Local testing ────────────────────────────────────────────────────
test-all: test-unit test-integration test-coverage

test-unit:
	@echo "=== Running unit tests ==="
	$(PYTEST) $(TEST_DIR) -m unit -v

test-integration:
	@echo "=== Running integration tests ==="
	$(PYTEST) $(TEST_DIR) -m integration -v --timeout=120

test-coverage:
	@echo "=== Running coverage ==="
	$(PYTEST) $(TEST_DIR) \
		--cov=$(PACKAGE) \
		--cov-report=term-missing \
		--cov-report=html:coverage_html \
		--cov-fail-under=95 \
		-v

# ─── Docker testing ───────────────────────────────────────────────────
docker-test:
	@echo "=== Running tests in Docker ==="
	$(COMPOSE) run --rm test

docker-shell:
	@echo "=== Starting shell in Docker ==="
	$(COMPOSE) run --rm shell

docker-benchmark:
	@echo "=== Running benchmarks in Docker ==="
	$(COMPOSE) --profile benchmark run --rm benchmark

docker-build:
	$(COMPOSE) build

# ─── Docker Jupyter ────────────────────────────────────────────────────
docker-jupyter:
	@echo "=== Starting Jupyter Notebook ==="
	$(COMPOSE) up -d jupyter
	@echo ""
	@echo "Jupyter Notebook disponível em: http://localhost:8888"
	@echo "Token: nenhum (acesso livre)"
	@echo "Para parar: make docker-jupyter-stop"

docker-jupyter-stop:
	$(COMPOSE) stop jupyter

docker-jupyter-logs:
	$(COMPOSE) logs -f jupyter

# ─── Shell ────────────────────────────────────────────────────────────
shell:
	@echo "=== Starting PySpark shell ==="
	python -c "from pyspark.sql import SparkSession; \
		spark = SparkSession.builder \
			.appName('spark-eda-dev') \
			.master('local[*]') \
			.config('spark.sql.shuffle.partitions', '4') \
			.getOrCreate(); \
		print('Spark session ready:', spark); \
		import code; code.interact(local=dict(locals(), **globals()))"

# ─── Build ────────────────────────────────────────────────────────────
build:
	@echo "=== Building package ==="
	python -m build

# ─── Clean ────────────────────────────────────────────────────────────
clean:
	@echo "=== Cleaning artifacts ==="
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .pytest_cache/
	rm -rf coverage_html/
	rm -rf $(BENCH_DIR)/
	rm -rf .coverage
	rm -rf __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete