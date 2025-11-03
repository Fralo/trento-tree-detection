# Tree Detection API

A FastAPI application with PostgreSQL integration for managing tree detection data.

## Features

- FastAPI with Python 3.12
- PostgreSQL database
- Pydantic models for data validation
- Alembic for database migrations
- Docker setup with hot reload
- Two endpoints: GET (list trees) and POST (create tree)

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and endpoints
│   ├── models.py        # Pydantic and SQLAlchemy models
│   └── database.py      # Database configuration
├── alembic/
│   ├── versions/        # Migration scripts
│   ├── env.py          # Alembic environment configuration
│   └── script.py.mako  # Migration template
├── alembic.ini          # Alembic configuration
├── entrypoint.sh        # Docker entrypoint with migration runner
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Quick Start

1. Build and start the containers:
```bash
docker-compose up --build
```

The application will automatically:
- Start PostgreSQL database
- Run Alembic migrations to create the `trees` table
- Start the FastAPI application with hot reload

2. The API will be available at `http://localhost:8000`

3. Access the interactive API documentation at `http://localhost:8000/docs`

## API Endpoints

### GET /trees
List all trees in the database.

**Response:**
```json
[
  {
    "id": 1,
    "latitude": 45.123,
    "longitude": -122.456,
    "source_file": "image1.jpg",
    "bbox_xmin": 100,
    "bbox_ymin": 200,
    "bbox_xmax": 300,
    "bbox_ymax": 400
  }
]
```

### POST /trees
Create a new tree entry.

**Request Body:**
```json
{
  "latitude": 45.123,
  "longitude": -122.456,
  "source_file": "image1.jpg",
  "bbox_xmin": 100,
  "bbox_ymin": 200,
  "bbox_xmax": 300,
  "bbox_ymax": 400
}
```

**Response:**
```json
{
  "id": 1,
  "latitude": 45.123,
  "longitude": -122.456,
  "source_file": "image1.jpg",
  "bbox_xmin": 100,
  "bbox_ymin": 200,
  "bbox_xmax": 300,
  "bbox_ymax": 400
}
```

## Development

The application supports hot reload. Any changes to files in the `app/` directory will automatically restart the server.

## Database Migrations

This project uses Alembic for database migrations.

### Automatic Migrations on Startup

When you run `docker-compose up`, the application automatically runs `alembic upgrade head` to apply all pending migrations before starting the FastAPI server.

### Creating New Migrations

To create a new migration after modifying models:

1. Access the running container:
```bash
docker-compose exec app bash
```

2. Generate a new migration:
```bash
alembic revision --autogenerate -m "description of changes"
```

3. Review the generated migration file in `alembic/versions/`

4. The migration will be automatically applied on next container restart

### Manual Migration Commands

Run migrations manually:
```bash
docker-compose exec app alembic upgrade head
```

Rollback last migration:
```bash
docker-compose exec app alembic downgrade -1
```

View migration history:
```bash
docker-compose exec app alembic history
```

View current migration:
```bash
docker-compose exec app alembic current
```

## Database

- Database: PostgreSQL 16
- Default credentials:
  - User: postgres
  - Password: postgres
  - Database: trees_db
- Port: 5432

## Stop the Application

```bash
docker-compose down
```

To remove volumes as well:
```bash
docker-compose down -v
```
