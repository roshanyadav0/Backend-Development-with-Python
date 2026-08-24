pip install alembic --break-system-packages

alembic init migrations

alembic revision --autogenerate -m "initial"

alembic upgrade head