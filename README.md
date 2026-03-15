# OpenTrade

OpenTrade is an AI crypto trading dashboard built with `Vue 3` and `FastAPI`.
It compares multiple AI models on the same market data, records structured decisions,
simulates spot execution, and visualizes portfolio performance in a single workspace.

## What It Does

- Streams Binance market data for `BTCUSDT`, `ETHUSDT`, and `SOLUSDT`
- Supports multiple AI providers with configurable `API Key`, `Base URL`, `Model`, and `Provider`
- Runs scheduled decision cycles with strict JSON output validation
- Simulates spot trading with isolated paper portfolios per model
- Tracks positions, orders, NAV, and multi-model return curves on the dashboard
- Stores audit data for decisions, strategy runs, and execution outcomes

## Current Scope

- Spot only
- Long only
- Symbols limited to `BTC`, `ETH`, and `SOL`
- Paper trading execution
- Multiple positions per model are allowed
- Configurable application timezone from `.env`

## Tech Stack

- Frontend: `Vue 3`, `Vite`, `Pinia`, `Vue Router`, `ECharts`
- Backend: `FastAPI`, `SQLAlchemy`, `Pydantic`, `OpenAI SDK`, `httpx`, `websockets`
- Storage: `SQLite` for the current MVP

## Project Structure

- `frontend/`: dashboard UI and browser-side utilities
- `backend/`: API, scheduler, market data, AI routing, and paper executor
- `.env`: local runtime configuration
- `docker-compose.yml`: local container orchestration

## Core Features

### 1. Model Configuration

Each AI model can be configured independently with:

- `API Key`
- `Base URL`
- `Model`
- `Provider`
- `temperature`
- `max_tokens`
- `timeout_seconds`
- strategy participation toggle

Secrets are encrypted before being stored in the backend database, and the UI only shows masked keys.

### 2. Market Data

- Binance WebSocket is used for realtime ticker updates
- Binance REST is used for historical K-line retrieval
- Dashboard prices update live
- Technical indicators are computed from historical K-line data

### 3. Decision Engine

On each strategy cycle, every enabled model receives:

- current market snapshot
- historical K-lines
- derived indicators
- recent decisions
- current positions
- portfolio state

The model must return strict JSON. Invalid, empty, or failed responses fall back to `HOLD`.

### 4. Paper Trading

Each model has an isolated paper account with:

- cash balance
- positions
- average entry price
- realized and unrealized PnL
- order history
- NAV series

Execution includes simulated fees and slippage.

## Local Development

### Backend

If you use Conda:

```bash
cd backend
conda activate myenv
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If you use a virtual environment:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment

Copy `.env.example` to `.env` and update the values before running the project.

Important settings:

```env
APP_NAME=OpenTrade
APP_TIMEZONE=Asia/Shanghai
DATABASE_URL=sqlite:///./data/opentrade.db
DECISION_INTERVAL_SECONDS=300
BINANCE_WS_URL=wss://stream.binance.com:9443/stream
BINANCE_REST_URL=https://api.binance.com
```

## Timezone

Application time is configurable from `.env` via:

```env
APP_TIMEZONE=Asia/Shanghai
```

Both backend API responses and frontend time formatting use this value.

## Database

The backend automatically initializes the SQLite database on startup.
Current default path:

```text
backend/data/opentrade.db
```

## Privacy and Secret Handling

- `.env` is ignored by `.gitignore`
- `.env.*` files are ignored, except `.env.example`
- runtime database files under `backend/data/` are ignored
- no obvious API keys or private key files were found during a workspace scan

## Notes

- This is an MVP and not a production trading system
- The current executor is paper-only
- Frontend build currently emits a large bundle warning because of charting dependencies, but it builds successfully
