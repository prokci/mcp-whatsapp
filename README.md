# MCP WhatsApp: Hybrid Autonomous Agent Bridge

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Protocol-blue.svg)](https://modelcontextprotocol.io)
[![Pydoll](https://img.shields.io/badge/Browser-Pydoll%20CDP-orange.svg)](https://github.com/automa-io/pydoll)
[![Neonize](https://img.shields.io/badge/WhatsApp-Neonize%20%2F%20Whatsmeow-25D366.svg?logo=whatsapp)](https://github.com/krypton-byte/neonize)
[![PostgreSQL](https://img.shields.io/badge/Storage-pgvector%20%2F%20Postgres-4169E1.svg?logo=postgresql)](https://www.postgresql.org)

An MCP (Model Context Protocol) server and FastAPI service that bridges AI workflow engines with WhatsApp. 

It implements a **dual-engine architecture**:
1. **Inbound & Sync Engine (Neonize / whatsmeow)**: High-speed binary protocol hook for real-time message listening, file downloads, history synchronization, and contact/LID resolution backed by PostgreSQL.
2. **Outbound Engine (Pydoll CDP Automation)**: Stealth, browser-level Chrome automation executing message dispatches, attachment uploads, and optional human-in-the-loop review.

---

## Table of Contents

- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Installation and First-Time Pairing](#installation-and-first-time-pairing)
  - [1. Neonize Protocol Pairing](#1-neonize-protocol-pairing)
  - [2. WhatsApp Web Browser Pairing](#2-whatsapp-web-browser-pairing)
- [Deployment](#deployment)
  - [Docker Compose (Production)](#docker-compose-production)
  - [Local Development](#local-development)
- [MCP & HTTP Endpoints](#mcp--http-endpoints)
  - [MCP Tools](#mcp-tools)
  - [Streaming Endpoints](#streaming-endpoints)
- [Client Integration](#client-integration)
  - [n8n Workflow Setup](#n8n-workflow-setup)
  - [Claude Desktop / Cursor Configuration](#claude-desktop--cursor-configuration)
- [Testing](#testing)

---

## Key Features

- **Standard MCP SSE Interface**: Exposes tools compliant with the Model Context Protocol over Server-Sent Events (`/sse` and `/messages`).
- **Human-In-The-Loop Confirmation**: MCP tools accept `need_user_confirmation=True` to navigate to the chat and populate the text or attachment without pressing send.
- **Queue & Humanization**: Sequential task processing (`WebAppQueue`) with configurable humanized cursor movement, random step delays, and cross-platform clipboard pasting (`pyclip`).
- **Dual Verification Database**: Inbound messages, attachments, and historical conversations are mapped and stored in PostgreSQL (`whatsapp_messages`), matching user JIDs and LIDs.
- **Headless Docker Support**: Ships with an `entrypoint.sh` providing virtual frame buffering (`Xvfb`), lock-file cleanup, and Chrome flags designed to prevent background throttling and CDP detachment.

---

## Project Structure

```
├── .dockerignore
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh                # Xvfb runner, stale lock cleaner, and uvicorn starter
├── neomy_init.py                # Standalone DB and Neonize pairing script
├── requirements.txt
├── src
│   ├── main.py                  # FastAPI server, FastMCP tools, and SSE transports
│   └── mcp_whatsapp
│       ├── data_base            # SQLAlchemy async database models and session manager
│       ├── mcp                  # MCP protocols, models, raw ASGI response handlers
│       ├── tasks                # Tasks (PydollSendMessage, PydollSendFile, etc.)
│       ├── utils                # Context singletons, helper routines, type handlers
│       └── web_app              # PydollContext, NeonizeContext, WebAppQueue, Policies
└── tests                        # Pytest suites verifying automation tasks
```

---

## Prerequisites

- **Docker & Docker Compose** (Recommended for deployment)
- **Python 3.12+** (For local development)
- **Google Chrome** (Stable channel)
- **PostgreSQL 17** (or containerized image `pgvector/pgvector:pg17`)
- System dependencies for browser automation: `xvfb`, `xclip`, `ffmpeg`, `libmagic1`

---

## Environment Configuration

Create a `.env` file (for local development) and `.env.docker` (for containerized runs) based on `.env.example`:

```bash
cp .env.example .env
```

| Variable | Description | Example |
| :--- | :--- | :--- |
| `USER_CHROME_DIR` | Absolute path to the host Chrome profile directory | `/home/user/.config/google-chrome` |
| `CHROME_PROFILE` | Chrome profile name containing an active session | `Profile 1` or `Default` |
| `DOCKER_USER_CHROME_DIR` | Path inside container where Chrome profile is mounted | `/home/.config/google-chrome` |
| `MCP_PORT` | Listening port for FastAPI / MCP server | `9831` |
| `PG_HOST` | Hostname of the PostgreSQL database | `mcp-whatsapp-db` (or `localhost`) |
| `PG_PORT` | Port for PostgreSQL connection | `5432` |
| `PG_DATABASE` | PostgreSQL database name | `postgres` |
| `PG_USERNAME` | Database username | `postgres` |
| `PG_PASSWORD` | Database password | `password` |
| `FOLDER_FILES` | Host directory containing attachments mounted to container | `/home/user/documents` |

---

## Installation and First-Time Pairing

WhatsApp requires two active authentication states: the Neonize binary client and the Chrome browser profile.

### 1. Neonize Protocol Pairing

The Neonize engine needs to connect and authenticate with WhatsApp's multi-device network. Run the initialization script locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python neomy_init.py
```
Scan the terminal QR code using WhatsApp on your primary phone (**Linked Devices -> Link a Device**). Once authenticated, session credentials are saved directly to the database.

### 2. WhatsApp Web Browser Pairing

Pydoll controls Chrome via DevTools Protocol and uses a saved profile to bypass repeated logins:

1. Launch Google Chrome locally pointing to the directory specified in `USER_CHROME_DIR`:
   ```bash
   google-chrome --user-data-dir="/path/to/chrome-data" --profile-directory="Profile 1"
   ```
2. Navigate to `https://web.whatsapp.com` and link your device.
3. Close the browser completely.

---

## Deployment

### Docker Compose (Production)

The production configuration handles PostgreSQL, the Xvfb display, Chrome dependencies, and the API server in an isolated environment.

1. Ensure `.env.docker` is configured.
2. Start the services:
   ```bash
   docker compose up -d --build
   ```
3. Check container logs:
   ```bash
   docker compose logs -f mcp-whatsapp
   ```

### Local Development

Run the server with Uvicorn:

```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 9831 --reload
```

---

## MCP & HTTP Endpoints

### MCP Tools

Clients connected to the MCP protocol have access to the following registered tools:

#### 1. `send_whatsapp_message`
Sends a plain text message to a specific phone number.
- `phone_number` (*string*, required): Target number with country code (e.g., `"14155552671"`).
- `message` (*string*, required): The message body.
- `need_user_confirmation` (*boolean*, optional, default: `False`): If `True`, types the message in the input field without pressing ENTER.

#### 2. `send_whatsapp_file`
Uploads and sends an attachment document/image with an optional caption.
- `phone_number` (*string*, required): Target number with country code.
- `file_path` (*string*, required): Path to the target file.
- `message` (*string*, optional, default: `""`): Caption accompanying the file.
- `need_user_confirmation` (*boolean*, optional, default: `False`): If `True`, stages the document without sending.

#### 3. `get_chat_history`
Retrieves stored message records for a specific contact.
- `phone_number` (*string*, required): Phone number to query.

### Streaming Endpoints

- **`GET /sse`**: MCP SSE entrypoint used by agents to initialize sessions and stream tool call requests.
- **`POST /messages`**: MCP message receiver endpoint for tool call execution.
- **`GET /whatsapp-events`**: Real-time Server-Sent Events stream for external automation platforms (e.g., n8n). Emits incoming messages as JSON:
  ```json
  {
    "pushname": "John Doe",
    "sender": "14155552671",
    "is_from_me": false,
    "text": "Hello!",
    "chat_user": "14155552671@s.whatsapp.net",
    "file_path": "/app/data/dowland/document.pdf"
  }
  ```

---

## Client Integration

### n8n Workflow Setup

1. **Trigger (Incoming Events)**:
   - Add an **SSE Trigger** node.
   - Set the URL to `http://<HOST>:9831/whatsapp-events`.
2. **Actions (MCP Tool Calls)**:
   - Connect an **MCP Tool** or **HTTP Request** node to `http://<HOST>:9831/sse`.

### Claude Desktop / Cursor Configuration

Add the server to your `claude_desktop_config.json` or project's `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "whatsapp": {
      "url": "http://localhost:9831/sse"
    }
  }
}
```

---

## Testing

Run the test suite against an active test session:

```bash
export TEST_PHONE_NUMBER="14155552671"
pytest -v tests/test_pydoll_tasks.py
```