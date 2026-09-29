.PHONY: smoke test

smoke:
	docker compose up -d db
	docker compose run --build --rm worker
	docker compose run --rm worker iris-smoke

test:
	python -m pytest
