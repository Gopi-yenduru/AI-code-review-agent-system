# 🤖 AI Code Review Agent

**Multi-agent AI pipeline that automatically reviews GitHub Pull Requests using three specialized AI agents running in parallel.**

When a developer opens a PR or pushes code, a webhook triggers three AI agents (Security Auditor, Performance Analyst, Code Quality Judge) powered by Google Gemini. Results are merged and posted as a structured comment on the PR. A React dashboard provides review history, risk scores, and per-developer analytics.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Webhook                          │
│                    (PR opened / synchronized)                   │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│                     POST /webhook/github                        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   Verify     │──│   Fetch PR Diff  │──│  Trigger Review  │  │
│  │   Signature  │  │   (GitHub API)   │  │    Pipeline      │  │
│  └──────────────┘  └──────────────────┘  └────────┬─────────┘  │
│                                                    │            │
│  ┌─────────────────────────────────────────────────┘            │
│  │           LangGraph StateGraph (Parallel)                    │
│  │                                                              │
│  │  ┌──────────────┐ ┌────────────────┐ ┌────────────────┐     │
│  │  │  🔒 Security │ │ ⚡ Performance │ │ 📋 Quality     │     │
│  │  │   Auditor    │ │   Analyst      │ │   Judge        │     │
│  │  │  (Gemini)    │ │  (Gemini)      │ │  (Gemini)      │     │
│  │  └──────┬───────┘ └──────┬─────────┘ └──────┬─────────┘     │
│  │         └────────────────┼──────────────────┘               │
│  │                          ▼                                   │
│  │                   ┌─────────────┐                            │
│  │                   │  Merge Node │──→ Risk Score              │
│  │                   └──────┬──────┘                            │
│  │                          │                                   │
│  └──────────────────────────┘                                   │
│              │                    │                              │
│    ┌─────────▼─────────┐  ┌──────▼──────────┐                  │
│    │  Save to Database │  │  Post PR Comment │                  │
│    │   (PostgreSQL)    │  │   (GitHub API)   │                  │
│    └───────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    React Dashboard (Port 3000)                  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  📊 Overview │  │  📝 Review Detail│  │  👤 Developer    │  │
│  │  Dashboard   │  │  (3 Agent Panels)│  │     Stats        │  │
│  └──────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer               | Technology                              |
|--------------------|-----------------------------------------|
| **Backend**        | Python 3.11, FastAPI, Uvicorn           |
| **Agent Orchestration** | LangGraph, LangChain             |
| **LLM**           | Google Gemini 1.5 Pro (free tier)       |
| **Database**       | PostgreSQL 15, SQLAlchemy 2.0 (async)  |
| **Frontend**       | React 18, Vite, Tailwind CSS, Recharts |
| **GitHub**         | Webhooks, REST API (PyGithub)           |
| **Containerization** | Docker, Docker Compose               |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- A [Google Gemini API key](https://aistudio.google.com/) (free tier works)
- A [GitHub Personal Access Token](https://github.com/settings/tokens) with `repo` scope

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/ai-code-review-agent.git
cd ai-code-review-agent

# 2. Configure environment
cp .env.example .env
# Edit .env and fill in:
#   GEMINI_API_KEY=your_key
#   GITHUB_TOKEN=your_token
#   GITHUB_WEBHOOK_SECRET=any_random_string

# 3. Start all services
docker-compose up --build

# 4. Verify
# Backend:  http://localhost:8000/health
# API Docs: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

---

## 🔗 Connecting GitHub Webhooks

### Local Development (ngrok)

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Go to your GitHub repo → Settings → Webhooks → Add webhook
#   Payload URL: https://abc123.ngrok.io/api/v1/webhook/github
#   Content type: application/json
#   Secret: (same as GITHUB_WEBHOOK_SECRET in .env)
#   Events: Pull requests
```

### Production (Railway / Render)

1. Deploy the backend to Railway/Render
2. Set environment variables on the platform
3. Use the deployed URL as the webhook payload URL

---

## 📡 API Endpoints

| Method | Endpoint                              | Description                    |
|--------|---------------------------------------|--------------------------------|
| GET    | `/health`                             | Health check                   |
| POST   | `/api/v1/webhook/github`              | GitHub webhook receiver        |
| GET    | `/api/v1/reviews`                     | List reviews (paginated)       |
| GET    | `/api/v1/reviews/{id}`                | Review details                 |
| GET    | `/api/v1/analytics/overview`          | Global dashboard stats         |
| GET    | `/api/v1/analytics/developer/{user}`  | Per-developer analytics        |
| GET    | `/api/v1/analytics/repo/{owner/repo}` | Per-repository analytics       |

---

## 🤖 AI Agents

### 🔒 Security Auditor
Detects SQL injection, hardcoded secrets, XSS, insecure dependencies, exposed credentials, path traversal.

### ⚡ Performance Analyst
Identifies N+1 queries, inefficient loops, unnecessary DB calls, blocking I/O, missing pagination.

### 📋 Code Quality Judge
Evaluates naming conventions, SOLID principles, dead code, error handling, complexity. Returns quality score (0-100).

### Risk Score Formula
```
risk_score = (critical×4 + high×3 + medium×2 + low×1) / (total_issues × 4) × 100
```

---

## 📁 Project Structure

```
ai-code-review-agent/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Pydantic settings
│   ├── database.py           # Async SQLAlchemy
│   ├── models/               # DB models (Review, Issue, Developer)
│   ├── agents/               # LangGraph pipeline + 3 AI agents
│   ├── services/             # Business logic (review, github, analytics)
│   ├── routers/              # API routes (webhook, reviews, analytics)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/            # Dashboard, ReviewDetail, DeveloperStats
│   │   ├── components/       # Navbar, RiskScoreCard, IssueList, AgentResultPanel
│   │   └── api/client.js     # Axios API client
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 📄 License

MIT License — feel free to use, modify, and distribute.
