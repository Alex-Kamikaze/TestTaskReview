FROM python:3.11-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.8.6 /uv /uvx /bin/
RUN apt-get -y update && \
  apt-get install -y build-essential \
  libncursesw5-dev \
  libssl-dev \
  libsqlite3-dev \
  tk-dev \
  libgdbm-dev \
  libc6-dev \
  libbz2-dev \
  libffi-dev \
  zlib1g-dev \
  gcc

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN pip install --upgrade pip
COPY uv.lock pyproject.toml ./
RUN pip install --upgrade pip
COPY uv.lock pyproject.toml ./
RUN uv sync --locked --python-preference system

COPY . /app/
RUN /usr/bin/env DB_URI="sqlite://:memory:"  python manage.py collectstatic --no-input
EXPOSE 8000