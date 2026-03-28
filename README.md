# ShuttleKit

A shuttle tracking API built with FastAPI, with a Vite frontend.

## Setup

### 1. Create and activate the virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install fastapi uvicorn
```

> Or once a `requirements.txt` exists: `pip install -r requirements.txt`

## Running the API

```bash
uvicorn api.main:app --reload
```

API will be available at `http://localhost:8000`.

## Project Structure

```
api/        FastAPI backend
web/        Frontend (Vite)
```
