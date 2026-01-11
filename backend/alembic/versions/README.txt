This folder will contain Alembic migration scripts generated with:

    alembic revision --autogenerate -m "message"

and applied with:

    alembic upgrade head

Ensure your environment variable `SECUREHUB_DATABASE_URL` points to the correct database URL when running Alembic.
