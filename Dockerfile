FROM digitalmarketplace/base-api:latest

COPY instrumented_sqlqlchemy_engine.py /app/venv/lib/python3.6/site-packages/sqlalchemy/engine/default.py
