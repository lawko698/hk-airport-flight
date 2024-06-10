# Setup containers to run Airflow

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

########################
warehouse-migration:
	docker exec hk-airport-flights-server-1 yoyo develop --no-config-file --database postgres://hkairportuser:hkairport1234@warehouse:5432/airport ./migrations

warehouse-rollback:
	docker exec hk-airport-flights-server-1 yoyo rollback --no-config-file --database postgres://hkairportuser:hkairport1234@warehouse:5432/airport ./migrations
