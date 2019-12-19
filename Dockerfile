FROM digitalmarketplace/builder AS builder

RUN apt-get update && apt-get install -y \
    libpq-dev \
    --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ${APP_DIR}

RUN ${APP_DIR}/venv/bin/pip3 install --no-cache-dir -r requirements.txt

COPY . ${APP_DIR}

FROM digitalmarketplace/base-api:9.0.0-alpha

RUN apt-get update && apt-get install -y \
    libpq-dev \
    --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder ${APP_DIR} ${APP_DIR}
