#!/usr/bin/env bash
# ==============================================================================
# PMC Officer Query System - Startup Script
# ==============================================================================
# Usage: ./start.sh [--skip-docker] [--skip-seed] [--force-seed] [--help]
# ==============================================================================

set -e

# Color definitions
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Absolute Script Directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SKIP_DOCKER=false
SKIP_SEED=false
FORCE_SEED=false

# Parse CLI arguments
for arg in "$@"; do
  case $arg in
    --skip-docker)
      SKIP_DOCKER=true
      shift
      ;;
    --skip-seed)
      SKIP_SEED=true
      shift
      ;;
    --force-seed)
      FORCE_SEED=true
      shift
      ;;
    -h|--help)
      echo -e "${BOLD}PMC Officer Query System Startup Script${NC}"
      echo ""
      echo "Usage: ./start.sh [options]"
      echo ""
      echo "Options:"
      echo "  --skip-docker   Skip launching the Docker metadata-db container"
      echo "  --skip-seed     Skip database template check and seeding"
      echo "  --force-seed    Force re-seeding templates and re-computing embeddings"
      echo "  -h, --help      Display this help message"
      exit 0
      ;;
  esac
done

echo -e "${BOLD}${CYAN}====================================================${NC}"
echo -e "${BOLD}${CYAN}      PMC Officer Query System Startup              ${NC}"
echo -e "${BOLD}${CYAN}====================================================${NC}"

# Detect Python & Tool Executables using Absolute Paths
if [ -f "$SCRIPT_DIR/backend/.venv/bin/activate" ]; then
  PYTHON_BIN="$SCRIPT_DIR/backend/.venv/bin/python"
  UVICORN_BIN="$SCRIPT_DIR/backend/.venv/bin/uvicorn"
  ALEMBIC_BIN="$SCRIPT_DIR/backend/.venv/bin/alembic"
elif [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
  PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
  UVICORN_BIN="$SCRIPT_DIR/.venv/bin/uvicorn"
  ALEMBIC_BIN="$SCRIPT_DIR/.venv/bin/alembic"
else
  PYTHON_BIN="$(which python3 2>/dev/null || echo python3)"
  UVICORN_BIN="$(which uvicorn 2>/dev/null || echo uvicorn)"
  ALEMBIC_BIN="$(which alembic 2>/dev/null || echo alembic)"
fi

# Cleanup handler for background processes
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo -e "${YELLOW}Stopping PMC Officer Query System services...${NC}"
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo -e "${YELLOW}Shutting down Backend API (PID: $BACKEND_PID)...${NC}"
    kill -TERM "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo -e "${YELLOW}Shutting down Frontend Dev Server (PID: $FRONTEND_PID)...${NC}"
    kill -TERM "$FRONTEND_PID" 2>/dev/null || true
  fi
  pkill -P $$ 2>/dev/null || true
  echo -e "${GREEN}All services stopped successfully.${NC}"
  exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# ------------------------------------------------------------------------------
# 1. Database Container (Docker pgvector)
# ------------------------------------------------------------------------------
if [ "$SKIP_DOCKER" = false ]; then
  echo -e "\n${BOLD}[1/4] Starting Metadata Database Container (pgvector)...${NC}"
  if command -v docker >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
      docker compose up -d metadata-db
    elif command -v docker-compose >/dev/null 2>&1; then
      docker-compose up -d metadata-db
    else
      echo -e "${YELLOW}Warning: Neither 'docker compose' nor 'docker-compose' command found. Skipping container start.${NC}"
    fi
  else
    echo -e "${YELLOW}Warning: Docker is not installed or not in PATH. Skipping container start.${NC}"
  fi
else
  echo -e "\n${YELLOW}[1/4] Skipping Docker database container startup (--skip-docker flag set).${NC}"
fi

# ------------------------------------------------------------------------------
# 2. Backend Environment & Database Readiness/Seed
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[2/4] Setting up Backend...${NC}"
cd "$SCRIPT_DIR/backend"

if [ "$SKIP_DOCKER" = false ]; then
  echo -e "${CYAN}Waiting for Metadata Database to accept connections on port 5433...${NC}"
  $PYTHON_BIN -c '
import socket, time, sys
for _ in range(30):
    try:
        s = socket.create_connection(("localhost", 5433), timeout=1)
        s.close()
        sys.exit(0)
    except Exception:
        time.sleep(1)
sys.exit(1)
' 2>/dev/null && echo -e "${GREEN}✓ Metadata Database is ready.${NC}" || echo -e "${YELLOW}Warning: Could not connect to localhost:5433. Proceeding anyway...${NC}"
fi

if [ "$SKIP_SEED" = false ]; then
  echo -e "${CYAN}Running database migrations...${NC}"
  $ALEMBIC_BIN upgrade head || echo -e "${YELLOW}Alembic migration check finished with warnings.${NC}"

  echo -e "${CYAN}Checking database templates and embeddings...${NC}"
  if [ "$FORCE_SEED" = true ]; then
    $PYTHON_BIN -m app.db.seed --force
  else
    $PYTHON_BIN -m app.db.seed
  fi
  echo -e "${GREEN}✓ Database check completed.${NC}"
else
  echo -e "${YELLOW}Skipping database seeding (--skip-seed flag set).${NC}"
fi

# ------------------------------------------------------------------------------
# 3. Launch Backend Service
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[3/4] Launching Unified FastAPI Backend...${NC}"
$UVICORN_BIN app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# ------------------------------------------------------------------------------
# 4. Launch Frontend Service
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[4/4] Launching React Frontend...${NC}"
cd "$SCRIPT_DIR/frontend"

if [ ! -d "node_modules" ]; then
  echo -e "${CYAN}node_modules missing. Installing npm packages...${NC}"
  npm install
fi

npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend dev server started (PID: $FRONTEND_PID)${NC}"

# ------------------------------------------------------------------------------
# Service Summary Banner
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}====================================================${NC}"
echo -e "${BOLD}${GREEN}  PMC Officer Query System is running!              ${NC}"
echo -e "${BOLD}${GREEN}====================================================${NC}"
echo -e "  ${BOLD}Web UI:${NC}            ${CYAN}http://localhost:5173${NC}"
echo -e "  ${BOLD}API Backend:${NC}       ${CYAN}http://localhost:8000${NC}"
echo -e "  ${BOLD}Swagger Docs:${NC}      ${CYAN}http://localhost:8000/docs${NC}"
echo -e "  ${BOLD}FastMCP Server:${NC}    ${CYAN}http://localhost:8000/mcp${NC}"
echo -e "  ${BOLD}Vanna AI 2.0 API:${NC}  ${CYAN}http://localhost:8000/api/vanna/v2${NC}"
echo -e "  ${BOLD}Metadata DB:${NC}       ${CYAN}localhost:5433${NC}"
echo -e "${BOLD}${GREEN}====================================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services.${NC}\n"

# Wait for background processes
wait
