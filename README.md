# DevH Unified API Platform
> Is now being rewritten in go.

A robust, modular FastAPI-based backend system designed to power the DevH ecosystem. This platform acts as a gateway for various services including AI chat interfaces, university resource management (IIITK), blog administration, world city data, and payment processing.

## 🏗 Architecture

The project is structured as a monolithic FastAPI application with modular routers (`APIRouter`) handling distinct functional domains.

### Key Modules
- **`ai/`**: Manages WebSocket connections for AI chat, integrating with Anthropic (Claude) via AWS Bedrock. Handles token usage tracking and credit deduction.
- **`api/wca/` (World Cities API)**: Provides endpoints for retrieving countries, states, and cities using MongoDB regex search.
- **`api/webagent/`**: A Selenium-based scraping tool (`web2md`) that converts websites to Markdown for LLM consumption.
- **`auth/`**: Implements Google OAuth2 flow for user authentication and session management using MongoDB.
- **`devh/`**: A headless CMS system for managing admins and blog posts with Role-Based Access Control (RBAC).
- **`iiitkres/`**: A specialized module for IIIT Kota resources, featuring note uploads, Gemini-powered note generation from images/audio, and a Llama-3 powered chatbot.
- **`stripe_pay/`**: Handles Stripe Checkout sessions and webhooks for credit purchases.
- **`tgbot/`**: Contains Pyrogram logic for Telegram bot integration.

## 🛠 Tech Stack

- **Framework**: FastAPI (Python 3.11)
- **Server**: Hypercorn (ASGI) with `uvloop`
- **Database**: MongoDB (via `motor` async driver)
- **AI Integration**:
    - Anthropic Claude (via AWS Bedrock)
    - Google Gemini (Generative AI)
    - Groq (Llama 3.1)
- **Authentication**: Google OAuth2, HTTP Basic Auth, API Key Headers
- **Background Tasks**: `APScheduler`
- **Browser Automation**: Selenium (Chrome)

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11+
- MongoDB Instance
- Chrome/Chromium (for Web Agent)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/devh-api.git
cd devh-api
```

### 2. Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the root directory. *See the "Security & Environment Variables" section below for required keys.*

### 5. Run Local Server
```bash
# Using uvicorn directly
uvicorn main:app --reload --port 8000

# OR using the provided Procfile command
hypercorn main:app --bind 0.0.0.0:8000
```

## 🐳 Docker Deployment

The project includes a `Dockerfile` and `docker-compose.yml` for containerized deployment.

```bash
# Build and run
docker-compose up -d --build
```

**Note:** The Dockerfile uses `python:3.11-slim` and installs necessary system dependencies for Chrome/Selenium and build tools.

## 🔄 CI/CD & Updates

The system includes a self-update mechanism via GitHub Webhooks (`internal/github.py`).
1. A POST request to `/internal/updated` with a valid signature triggers a `git pull`.
2. The `restart_server.sh` script creates a new background process and kills the old Hypercorn instance.

## 📚 API Documentation

Once running, access the interactive documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
