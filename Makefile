PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
PIP_INDEX_URL ?= https://example.com/simple

IMAGE ?= hackathon-app
TAG ?= local
CONTAINER ?= hackathon-app
PORT ?= 8080
URL ?= http://127.0.0.1:$(PORT)

STARTUP_DELAY_SECONDS ?= 40
REQUEST_THRESHOLD ?= 10
NOT_READY_SECONDS ?= 30
PARTICIPANT ?= $(USER)

.DEFAULT_GOAL := help
.PHONY: help venv install test lint format run docker-build docker-run docker-stop docker-logs smoke trip watch clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

$(BIN)/activate:
	$(PYTHON) -m venv $(VENV)

venv: $(BIN)/activate ## Create the virtualenv

install: venv ## Install app and dev dependencies
	$(BIN)/pip install -q -i $(PIP_INDEX_URL) -r requirements-dev.txt

test: ## Run unit tests
	$(BIN)/pytest -q

lint: ## Check code style
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

format: ## Auto-format code
	$(BIN)/ruff format .
	$(BIN)/ruff check --fix .

run: ## Run the app locally without Docker
	PORT=$(PORT) STARTUP_DELAY_SECONDS=$(STARTUP_DELAY_SECONDS) REQUEST_THRESHOLD=$(REQUEST_THRESHOLD) \
	NOT_READY_SECONDS=$(NOT_READY_SECONDS) PARTICIPANT=$(PARTICIPANT) $(BIN)/python -m app

docker-build: ## Build the Docker image
	docker build -t $(IMAGE):$(TAG) .

docker-run: docker-stop ## Run the image in the background
	docker run -d --name $(CONTAINER) -p $(PORT):8080 \
		-e STARTUP_DELAY_SECONDS=$(STARTUP_DELAY_SECONDS) \
		-e REQUEST_THRESHOLD=$(REQUEST_THRESHOLD) \
		-e NOT_READY_SECONDS=$(NOT_READY_SECONDS) \
		-e PARTICIPANT=$(PARTICIPANT) \
		$(IMAGE):$(TAG)
	@echo "Started. The app warms up for $(STARTUP_DELAY_SECONDS)s — try: make watch"

docker-stop: ## Stop and remove the container
	-@docker rm -f $(CONTAINER) >/dev/null 2>&1 || true

docker-logs: ## Follow container logs
	docker logs -f $(CONTAINER)

smoke: ## Call /live, /ready and /hello once
	@for p in /live /ready /hello; do \
		printf '%-7s ' $$p; curl -s -w '  [%{http_code}]\n' $(URL)$$p; \
	done

trip: ## Send REQUEST_THRESHOLD calls to /hello, then show /ready
	@for i in $$(seq 1 $(REQUEST_THRESHOLD)); do \
		curl -s -o /dev/null -w "hello #$$i [%{http_code}]\n" $(URL)/hello; \
	done
	@printf '/ready  '; curl -s -w '  [%{http_code}]\n' $(URL)/ready
	@printf '/live   '; curl -s -w '  [%{http_code}]\n' $(URL)/live

watch: ## Print /live and /ready status every second (Ctrl+C to stop)
	@while true; do \
		printf '%s  live=%s ready=%s\n' "$$(date +%T)" \
			"$$(curl -s -o /dev/null -w '%{http_code}' $(URL)/live)" \
			"$$(curl -s -o /dev/null -w '%{http_code}' $(URL)/ready)"; \
		sleep 1; \
	done

clean: docker-stop ## Remove virtualenv and caches
	rm -rf $(VENV) .pytest_cache .ruff_cache .coverage coveragereport test-results.xml
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
