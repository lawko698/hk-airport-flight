# Setup containers to run Prefect

up:
	docker compose  --profile server --profile minio --profile agent --profile cli --profile warehouse --env-file env up -d --build

spinup:
	up sleep 15 warehouse-migration

down:
	docker compose --profile server --profile minio --profile agent --profile cli --profile warehouse --env-file env down

cleanup:
	down -v 

cli:
	docker compose --env-file env run cli

format:
	docker exec hk-airport-flight-server-1 python -m black -S --line-length 79 /opt/prefect/flows

isort:
	docker exec hk-airport-flight-server-1 isort .

pytest:
	docker exec hk-airport-flight-server-1 pytest /opt/prefect/tests

type:
	docker exec hk-airport-flight-server-1 mypy --ignore-missing-imports /opt/prefect/flows

lint: 
	docker exec hk-airport-flight-server-1 flake8 /opt/prefect/flows

ci: isort format type lint pytest

########################
warehouse-migration:
	docker exec hk-airport-flight-server-1 yoyo develop --no-config-file --database postgres://hkairportuser:hkairport1234@warehouse:5432/airport ./migrations

warehouse-rollback:
	docker exec hk-airport-flight-server-1 yoyo rollback --no-config-file --database postgres://hkairportuser:hkairport1234@warehouse:5432/airport ./migrations
