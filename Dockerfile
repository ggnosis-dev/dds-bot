FROM python:3.14-slim

WORKDIR /app

# Install jemalloc and assign it as our memory allocator. Clear the apt cache afterwards.
RUN apt-get update && apt-get install -y --no-install-recommends libjemalloc2 \
    && rm -rf /var/lib/apt/lists/*
ENV LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libjemalloc.so.2

# Do not need virtual env as it is already isolated.
RUN pip install poetry
RUN poetry config virtualenvs.create false

# Get the dependencies.
COPY pyproject.toml poetry.lock ./

# Do not try to install our project as root package.
RUN poetry install --no-root

# Copy application code into /app.
COPY . .

CMD [ "python3", "main.py" ]