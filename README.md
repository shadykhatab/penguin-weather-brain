# PenguinWeather Backend

FastAPI backend for the PenguinWeather app.

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the template and add your API keys:

```bash
# Windows
copy env.template .env

# macOS/Linux
cp env.template .env
```

Edit the `.env` file:
- `WEATHER_API_KEY` - Your weather service API key
- `OPENAI_API_KEY` - Your OpenAI API key

### 5. Run the Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/weather?city={city}` | Get weather for a city |

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

"Deployment test."
