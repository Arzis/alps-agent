.PHONY: help setup dev up down logs test lint clean test-unit test-integration format worker

help:  ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## 首次项目初始化
	poetry install
	cp .env.example .env
	docker compose -f docker/docker-compose.yml up -d postgres redis milvus-standalone etcd minio
	sleep 10
	poetry run python scripts/init_db.py

dev:  ## 启动开发服务器(热重载)
	poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

up:  ## 启动所有Docker服务
	docker compose -f docker/docker-compose.yml up -d

down:  ## 停止所有Docker服务
	docker compose -f docker/docker-compose.yml down

logs:  ## 查看API服务日志
	docker compose -f docker/docker-compose.yml logs -f api

test:  ## 运行测试
	poetry run pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:  ## 运行单元测试
	poetry run pytest tests/unit/ -v

test-integration:  ## 运行集成测试
	poetry run pytest tests/integration/ -v

lint:  ## 代码检查
	poetry run ruff check src/ tests/
	poetry run ruff format --check src/ tests/
	poetry run mypy src/

format:  ## 代码格式化
	poetry run ruff format src/ tests/
	poetry run ruff check --fix src/ tests/

clean:  ## 清理
	docker compose -f docker/docker-compose.yml down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

worker:  ## 启动异步Worker
	poetry run arq src.infra.queue.task_queue.WorkerSettings
