# Tactera Backend

Python FastAPI backend for the Tactera football management game.

## Setup

### Prerequisites
- Python 3.8+
- pip

### Installation
```bash
cd backend
pip install -r requirements.txt
```

### Development
```bash
pip install -r requirements-dev.txt
```

## Running

### Development Server
```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
backend/
├── app/
│   ├── core/         # Core functionality (auth, config, database)
│   ├── models/       # SQLModel data models and schemas
│   ├── routes/       # FastAPI route handlers
│   ├── services/     # Business logic services
│   └── seed/         # Database seeding scripts
├── tests/            # Test files
└── requirements.txt  # Python dependencies
```

## Database

The application uses SQLite for development. Database file: `app/tactera.db`

### Seeding
Database is automatically seeded on startup if empty.

## Testing

```bash
python -m pytest tests/
```