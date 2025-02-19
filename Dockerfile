FROM python:3.11.10-slim AS base

ARG DEBIAN_FRONTEND=noninteractive

ENV PIP_NO_CACHE_DIR=1 \
		PIP_DISABLE_PIP_VERSION_CHECK=1 \
		POETRY_VIRTUALENVS_CREATE=1 \
		POETRY_VIRTUALENVS_IN_PROJECT=1 \
		POETRY_NO_INTERACTION=1 \
		POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apt-get update \
		&& apt-get upgrade -y \
		&& apt-get install -y --no-install-recommends \
			apt-utils make kmod libpq-dev gcc ca-certificates libffi-dev \
		&& rm -rf /var/lib/apt/lists/* \
		&& pip install -U --no-cache-dir pip \
		&& pip install --no-cache-dir poetry

RUN groupadd -r athena && useradd -rm -u 7723 -g athena athena
USER athena

WORKDIR /home/athena

COPY ./pyproject.toml ./poetry.lock /home/athena/

RUN poetry install --no-root --sync --only main && rm -rf $POETRY_CACHE_DIR


FROM python:3.11.10-slim

ENV PATH="/code/.venv/bin:$PATH"

RUN apt-get update \
		&& apt-get upgrade -y \
		&& apt-get install -y --no-install-recommends \
			apt-utils make kmod libpq-dev gcc ca-certificates libffi-dev \
		&& rm -rf /var/lib/apt/lists/*

RUN groupadd -r athena && useradd -rm -u 7723 -g athena athena \
	&& mkdir -p /code && chown -R athena:athena /code

USER athena

WORKDIR /code

COPY --from=base --chown=athena:athena \
	/home/athena/pyproject.toml /home/athena/poetry.lock /code/
COPY --from=base --chown=athena:athena /home/athena/.venv /code/.venv
COPY --chown=athena:athena ./app /code/app

CMD ["python", "app/main.py"]
