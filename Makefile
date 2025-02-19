DOCKER_IMAGE=genaiorchestrator-cbrm-client:latest
DOCKER_CONTAINER=chatbot_client_latest
PORT=7071

.PHONY: prepare-dev
prepare-dev:
	@echo "Preparing your local development environment..."; \
	POETRY_VIRTUALENVS_IN_PROJECT=1 poetry install --sync --with dev

.PHONY: lint
lint:
	@tput bold; echo "Running linter..."; tput sgr0; \
	POETRY_DONT_LOAD_DOTENV=1 poetry run pylint -E app/*.py

.PHONY: docker
docker:
	@tput bold; echo "Building docker image..."; tput sgr0; \
	docker build -t $(DOCKER_IMAGE) --no-cache .

.PHONY: run
run:
	@tput bold; echo "Running docker image..."; tput sgr0; \
		docker run -it -d --name $(DOCKER_CONTAINER) --restart always --env-file .env -v $(shell pwd)/logs:/code/logs -p $(PORT):$(PORT) $(DOCKER_IMAGE)
