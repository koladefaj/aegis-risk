.PHONY: proto up down build test lint clean migrate

# ─── Proto Compilation ──────────────────────────────────
proto:
	python -m grpc_tools.protoc \
		--proto_path=proto \
		--python_out=shared/aegis_shared/generated \
		--grpc_python_out=shared/aegis_shared/generated \
		--pyi_out=shared/aegis_shared/generated \
		proto/*.proto
	@echo "Proto stubs generated in shared/aegis_shared/generated/"

# ─── Docker ─────────────────────────────────────────────
up:
	docker-compose up -d
	@echo "All services started"

down:
	docker-compose down
	@echo "All services stopped"

build:
	docker-compose build
	@echo "All images built"

rebuild:
	docker-compose build --no-cache
	@echo "All images rebuilt from scratch"

logs:
	docker-compose logs -f

ps:
	docker-compose ps


