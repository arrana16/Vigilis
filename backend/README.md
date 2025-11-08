# Vigilis Backend

Backend API for the Vigilis Emergency Services Dashboard.

## 📁 Folder Structure

```
backend/
├── api.py                      # Main FastAPI application
├── db.py                       # MongoDB connection
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
│
├── descriptions/              # 📚 All documentation files
│   ├── README.md
│   ├── QUICK_START.md
│   ├── MONGODB_SSL_FIX.md
│   ├── POLICE_CARS_README.md
│   ├── REDIS_QUICK_START.md
│   ├── REDIS_REALTIME_TRACKING.md
│   └── REDIS_SETUP_COMPLETE.md
│
├── redis/                     # 🚗 Real-time location tracking (Redis)
│   ├── __init__.py
│   ├── README.md
│   ├── redis_client.py        # Redis operations
│   ├── location_sync.py       # Sync Redis → MongoDB (10s)
│   ├── car_simulator.py       # Simulate car movement
│   ├── test_redis_system.py   # Test suite
│   └── demo_realtime_tracking.py  # Live demo
│
├── police_cars.py             # 🚓 Police car management (MongoDB)
├── test_police_cars.py        # Police cars test script
│
├── suggest.py                 # 💡 AI suggestions for incidents
├── update.py                  # 📝 Incident reports & updates
│
└── polizia_agent/            # 🤖 AI Agent for incident analysis
    ├── agent.py
    └── tools.py
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your MongoDB URI and Redis settings
```

### 3. Start Redis (for real-time tracking)

```bash
# macOS
brew install redis
brew services start redis

# Verify
redis-cli ping  # Should return: PONG
```

### 4. Run the Server

```bash
uvicorn api:app --reload
```

Server starts at: http://localhost:8000

## 📚 Documentation

All documentation is in the **`descriptions/`** folder:

-   **Getting Started**: `descriptions/QUICK_START.md`
-   **MongoDB Setup**: `descriptions/MONGODB_SSL_FIX.md`
-   **Police Cars API**: `descriptions/POLICE_CARS_README.md`
-   **Real-time Tracking**: `descriptions/REDIS_QUICK_START.md`

## 🔧 Key Components

### FastAPI Application (`api.py`)

Main REST API with endpoints for:

-   Incident management
-   Police car CRUD operations
-   Real-time location tracking
-   WebSocket streaming
-   AI chat assistant

### Police Car System (`police_cars.py`)

MongoDB-based system for:

-   Creating/managing police cars
-   Dispatching cars to incidents
-   Tracking dispatch history
-   Status management (inactive, dispatched, en_route, on_scene, returning)

### Redis Real-Time Tracking (`redis/`)

High-frequency location tracking:

-   **1-second updates** stored in Redis
-   **10-second sync** to MongoDB
-   **WebSocket streaming** for live tracking
-   **Car simulation** for testing

### AI Agent (`polizia_agent/`)

Incident analysis and suggestions:

-   Chat interface
-   Historical incident lookup
-   AI-powered recommendations

## 🧪 Testing

### Test Redis System

```bash
python redis/test_redis_system.py
```

### Test Police Cars

```bash
python test_police_cars.py
```

### Run Demo

```bash
python redis/demo_realtime_tracking.py
```

## 📡 API Endpoints

### Incidents

-   `POST /incident/summary` - Get incident summary
-   `POST /incident/suggestions` - Get AI suggestions
-   `POST /incident/report` - Generate report
-   `POST /incident/conclude` - Conclude incident

### Police Cars (MongoDB)

-   `POST /police/cars` - Create police car
-   `GET /police/cars` - Get all cars
-   `GET /police/cars/{car_id}` - Get specific car
-   `POST /police/dispatch` - Dispatch car to incident
-   `GET /police/available` - Get available cars

### Real-Time Tracking (Redis)

-   `GET /police/realtime/{car_id}` - Get real-time position
-   `GET /police/realtime` - Get all positions
-   `POST /police/nearby` - Find nearby cars
-   `WS /ws/track/{car_id}` - WebSocket stream

### Simulator

-   `POST /simulator/add/{car_id}` - Add to simulator
-   `DELETE /simulator/remove/{car_id}` - Remove from simulator

### System

-   `GET /health` - Health check
-   `GET /stats` - System statistics

## 🔐 Environment Variables

Required in `.env`:

```env
# MongoDB
MONGO_URI=mongodb+srv://...

# Redis (optional, defaults shown)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Google AI
GOOGLE_API_KEY=your_key_here
```

## 📊 Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│   MongoDB   │────▶│  Knowledge  │
│     API     │     │  (Storage)  │     │    Base     │
└─────────────┘     └─────────────┘     └─────────────┘
       │                    ▲
       │                    │
       ▼                    │
┌─────────────┐     Sync (10s)
│    Redis    │────────────┘
│ (Real-time) │
└─────────────┘
       ▲
       │ (1s updates)
       │
┌─────────────┐
│     Car     │
│  Simulator  │
└─────────────┘
```

## 🛠️ Development

### Project Structure

-   **Core files** at root level
-   **Documentation** in `descriptions/`
-   **Redis services** in `redis/`
-   **Tests** alongside relevant modules

### Adding New Features

1. Core API changes → `api.py`
2. Database operations → `police_cars.py` or `db.py`
3. Redis features → `redis/` folder
4. Documentation → `descriptions/` folder

## 📖 Learn More

-   **API Documentation**: http://localhost:8000/docs (Swagger UI)
-   **Full Documentation**: See `descriptions/` folder
-   **Redis System**: See `redis/README.md`

## 🐛 Troubleshooting

### MongoDB SSL Errors

See: `descriptions/MONGODB_SSL_FIX.md`

### Redis Connection Issues

```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

### Import Errors

Make sure you're in the correct directory:

```bash
cd backend
python api.py  # ❌ Wrong
uvicorn api:app --reload  # ✅ Correct
```

## 🎯 Next Steps

1. ✅ Start Redis server
2. ✅ Configure `.env` file
3. ✅ Run tests to verify setup
4. ✅ Start the API server
5. ✅ Create some police cars
6. ✅ Watch them move in real-time!

---

For detailed documentation, see the **`descriptions/`** folder.
