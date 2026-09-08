.PHONY: install test check run worker up down seed admin

install:
	python -m pip install -r requirements.txt

test:
	pytest -q

check:
	python -m compileall -q app scripts
	node --check web/app.js
	git diff --check

run:
	uvicorn app.main:app --reload

worker:
	python -m app.workers.submission_worker

up:
	docker compose up --build

down:
	docker compose down

seed:
	python -m scripts.seed_demo

admin:
	python -m scripts.bootstrap_admin
