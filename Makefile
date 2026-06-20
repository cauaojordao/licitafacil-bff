.PHONY: help install install-dev test lint format clean \
        docker-build docker-up docker-down docker-logs \
        infra-up infra-down \
        prefect-run prefect-server prefect-serve prefect-stop

# ==============================================================================
# HELP
# ==============================================================================

help:
	@echo "LicitaFacil BFF"
	@echo "==============================="
	@echo "install          - Instalar dependências"
	@echo "install-dev      - Instalar dependências de desenvolvimento"
	@echo "test             - Executar todos os testes"
	@echo "lint             - Executar validações"
	@echo "format           - Formatar código"
	@echo "clean            - Limpar artefatos"
	@echo ""
	@echo "docker-build     - Build das imagens"
	@echo "docker-up        - Subir todos os containers"
	@echo "docker-down      - Derrubar containers"
	@echo "docker-logs      - Logs dos containers"
	@echo ""
	@echo "infra-up         - Subir Mongo + Kafka + ZooKeeper"
	@echo "infra-down       - Derrubar infraestrutura"
	@echo ""
	@echo "prefect-run      - Executar pipeline uma vez"
	@echo "prefect-server   - Iniciar dashboard Prefect"
	@echo "prefect-serve    - Iniciar deployment agendado"
	@echo "prefect-stop     - Parar processos Prefect"

# ==============================================================================
# INSTALL
# ==============================================================================

install:
	pip install -e libs/common
	pip install -e libs/domain
	pip install -e libs/clients
	pip install -e libs/utils
	pip install -e apps/api
	pip install -e apps/consumer
	pip install -e apps/cronjob
	pip install -e apps/spark

install-dev: install
	pip install -e "libs/common[dev]"
	pip install -e "apps/api[dev]"
	pip install -e "apps/consumer[dev]"
	pip install -e "apps/cronjob[dev]"
	pip install -e "apps/spark[dev]"

# ==============================================================================
# TESTS
# ==============================================================================

test:
	pytest apps/api/tests
	pytest apps/consumer/tests
	pytest apps/cronjob/tests
	pytest apps/spark/tests

test-api:
	pytest apps/api/tests -v

test-consumer:
	pytest apps/consumer/tests -v

test-cronjob:
	pytest apps/cronjob/tests -v

test-spark:
	pytest apps/spark/tests -v

# ==============================================================================
# QUALITY
# ==============================================================================

lint:
	ruff check .
	mypy apps/api/src apps/ingestion/src apps/processor/src apps/maintenance/src \
		libs/common libs/clients orchestrate_prefect.py

format:
	ruff format .
	ruff check --fix .

# ==============================================================================
# CLEAN
# ==============================================================================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

# ==============================================================================
# DOCKER
# ==============================================================================

docker-build:
	docker-compose -f infra/docker/docker-compose.yml build

docker-up:
	docker-compose -f infra/docker/docker-compose.yml up -d

docker-down:
	docker-compose -f infra/docker/docker-compose.yml down

docker-logs:
	docker-compose -f infra/docker/docker-compose.yml logs -f

# ==============================================================================
# INFRA
# ==============================================================================

infra-up:
	docker-compose -f infra/docker/docker-compose.yml up -d mongodb zookeeper kafka

infra-down:
	docker-compose -f infra/docker/docker-compose.yml down

# ==============================================================================
# PREFECT
# ==============================================================================

prefect-run: infra-up
	python orchestrate_prefect.py

prefect-server:
	prefect server start

prefect-serve: infra-up
	python orchestrate_prefect.py serve

prefect-stop:
	pkill -f "prefect server" || true
	pkill -f "orchestrate_prefect" || true
	pkill -f "prefect agent" || true