# AI Stock & Crypto Analyzer (Neural Intelligence System)

A high-performance, distributed trading intelligence platform that combines machine learning, sentiment analysis, and multi-agent orchestration to provide real-time signals and trade journaling for Stocks, Crypto, and Commodities.

## 🚀 Key Features

- **Multi-Agent Orchestration:** Uses a "Debate Agent" and "Security Guard" architecture to refine signals and protect proprietary model workflows.
- **Neural Engines:** Integrated XGBoost and Ensemble models for price prediction and regime classification.
- **Sentiment Analysis:** Real-time news scraping (Yahoo Finance, Google News) with VADER intensity analysis.
- **Trade Journal:** Full-lifecycle trade tracking with automated target resolution (Points, Amount, or %).
- **Radar Dashboard:** High-confidence BUY/SELL signals with real-time browser notifications.
- **Production Ready:** Fully containerized with Docker, Nginx gateway, and environment-based configuration.

## 🏗️ Architecture

The system is built as a microservice mesh:
- **API Gateway (Nginx):** Unified entry point for all services.
- **Core Orchestrator (FastAPI):** Controls the data flow between agents and neural engines.
- **Intelligence Services:**
  - `auth-service`: Google OAuth 2.0 & JWT management.
  - `ml-service`: Neural inference and model serving.
  - `forecast-service`: Time-series forecasting.
  - `market-service`: Real-time data fetching (NSE, CCXT, YFinance).
  - `trading-service`: Broker abstraction and paper trading execution.

## 🛠️ Tech Stack

- **Frontend:** React, Tailwind CSS, Lucide Icons, Vite.
- **Backend:** Python, FastAPI, SQLAlchemy.
- **Database:** PostgreSQL (Core), SQLite (Feedback & Radar).
- **ML/DS:** Pandas, XGBoost, Scikit-learn, VADER.
- **Infrastructure:** Docker, Docker Compose, Nginx.

## 🏁 Getting Started

### Prerequisites
- Docker & Docker Compose
- Google OAuth Client ID (for Authentication)

### Installation
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd stock-crypto-analyzer
   ```
2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your secrets
   ```
3. Launch the system:
   ```bash
   docker-compose up -d --build
   ```
4. Access the UI:
   Navigate to `http://localhost:8000` (or your production domain).

## 🔒 Security
This platform implements a **SecureCoreGuard** layer that obfuscates internal model workflows using SHA-256 salting, ensuring proprietary technical details remain private while providing actionable intelligence to users.

## 📜 License
Proprietary / Private. Initial training phase enabled for public access.
