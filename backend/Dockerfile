FROM python:3.12-slim

WORKDIR /code

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /code/app
COPY ./alembic /code/alembic
COPY ./alembic.ini /code/alembic.ini
COPY ./entrypoint.sh /code/entrypoint.sh

RUN chmod +x /code/entrypoint.sh

CMD ["/code/entrypoint.sh"]
