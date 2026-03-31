.PHONY: install train up down test clean

install:
	pip install -r requirements.txt

train:
	dvc repro

up:
	docker-compose up --build -d

down:
	docker-compose down

test:
	PYTHONPATH=. pytest tests/

lint:
	python -m flake8 src/ app.py

validate:
	PYTHONPATH=. python src/validate_model.py

helm-lint:
	helm lint charts/iris-api/

ci: lint test validate helm-lint

clean:
	rm -rf mlruns/ .dvc/cache/ dvc.lock .hydra/
