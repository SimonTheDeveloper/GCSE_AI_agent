#!/usr/bin/env bash
set -euo pipefail

# Start FastAPI (uvicorn) and React dev server in parallel without Docker
# Requirements:
# - Python venv with backend deps (fastapi, uvicorn, boto3, python-dotenv)
# - Node with frontend deps installed

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/.dev-logs"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# Default API URL for frontend
export REACT_APP_API_URL=${REACT_APP_API_URL:-http://localhost:8001}
export BROWSER=${BROWSER:-none}  # prevent CRA from auto-opening browser

run_prefixed() {
  # usage: run_prefixed "[prefix]" "<logfile>" <cmd> [args...]
  local prefix="$1"; shift
  local logfile="$1"; shift
  # stdout and stderr prefixed and tee'd to logfile
  exec "$@" \
    > >(awk -v p="$prefix" '{ print p, $0 }' | tee -a "$logfile") \
    2> >(awk -v p="$prefix" '{ print p, $0 }' | tee -a "$logfile" >&2)
}

start_backend() (
  cd "$BACKEND_DIR"
  ROOT_VENV_DIR="$ROOT_DIR/.venv"
  ROOT_VENV_PY="$ROOT_VENV_DIR/bin/python"
  ROOT_VENV_PIP="$ROOT_VENV_DIR/bin/pip"
  VENV_DIR="$BACKEND_DIR/.venv"
  VENV_PY="$VENV_DIR/bin/python"
  VENV_PIP="$VENV_DIR/bin/pip"

  echo "[dev] backend logs -> $BACKEND_LOG"

  if [ -x "$ROOT_VENV_PY" ] && [ -x "$ROOT_VENV_PIP" ]; then
    echo "[dev] using repo root .venv ($ROOT_VENV_DIR)"
    if ! "$ROOT_VENV_PY" -c 'import fastapi, uvicorn, boto3, dotenv, pydantic, multipart, requests; import openai, pytesseract; from PIL import Image as _Img; import jose' >/dev/null 2>&1; then
      echo "[dev] installing backend deps into root .venv"
      "$ROOT_VENV_PIP" install --upgrade pip >/dev/null 2>&1 || true
      "$ROOT_VENV_PIP" install fastapi uvicorn boto3 python-dotenv pydantic python-multipart pillow pytesseract openai requests 'python-jose[cryptography]'
    fi
    if ! command -v tesseract >/dev/null 2>&1; then
      echo "[dev] note: 'tesseract' binary not found; OCR will be disabled until you install it (e.g. 'brew install tesseract')"
    fi
    echo "[dev] starting backend (uvicorn) on :8001"
    PYTHONUNBUFFERED=1 run_prefixed "[backend]" "$BACKEND_LOG" \
      "$ROOT_VENV_PY" -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
  elif [ -x "$VENV_PY" ] && [ -x "$VENV_PIP" ]; then
    echo "[dev] using backend .venv ($VENV_DIR)"
    if ! "$VENV_PY" -c 'import fastapi, uvicorn, boto3, dotenv, pydantic, multipart, requests; import openai, pytesseract; from PIL import Image as _Img; import jose' >/dev/null 2>&1; then
      echo "[dev] installing backend deps into backend .venv"
      "$VENV_PIP" install --upgrade pip >/dev/null 2>&1 || true
      "$VENV_PIP" install fastapi uvicorn boto3 python-dotenv pydantic python-multipart pillow pytesseract openai requests 'python-jose[cryptography]'
    fi
    if ! command -v tesseract >/dev/null 2>&1; then
      echo "[dev] note: 'tesseract' binary not found; OCR will be disabled until you install it (e.g. 'brew install tesseract')"
    fi
    echo "[dev] starting backend (uvicorn) on :8001"
    PYTHONUNBUFFERED=1 run_prefixed "[backend]" "$BACKEND_LOG" \
      "$VENV_PY" -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
  elif command -v poetry >/dev/null 2>&1 && [ -f pyproject.toml ]; then
    echo "[dev] ensuring backend deps with poetry"
    poetry install --no-interaction --no-ansi
    echo "[dev] starting backend (poetry) on :8001"
    PYTHONUNBUFFERED=1 run_prefixed "[backend]" "$BACKEND_LOG" \
      poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8001
  else
    echo "[dev] ensuring backend deps with pip"
    if ! python3 -c 'import fastapi, uvicorn, boto3, dotenv, pydantic, multipart, requests; import openai, pytesseract; from PIL import Image as _Img; import jose' >/dev/null 2>&1; then
      pip3 install --upgrade pip >/dev/null 2>&1 || true
      pip3 install fastapi uvicorn boto3 python-dotenv pydantic python-multipart pillow pytesseract openai requests 'python-jose[cryptography]'
    fi
    if ! command -v tesseract >/dev/null 2>&1; then
      echo "[dev] note: 'tesseract' binary not found; OCR will be disabled until you install it (e.g. 'brew install tesseract')"
    fi
    echo "[dev] starting backend (system) on :8001"
    PYTHONUNBUFFERED=1 run_prefixed "[backend]" "$BACKEND_LOG" \
      uvicorn main:app --reload --host 0.0.0.0 --port 8001
  fi
)

start_frontend() (
  cd "$FRONTEND_DIR"
  echo "[dev] frontend logs -> $FRONTEND_LOG"
  if [ ! -d node_modules ]; then
    if [ -f package-lock.json ]; then
      echo "[dev] installing frontend deps with npm ci"
      npm ci
    else
      echo "[dev] installing frontend deps with npm install"
      npm install
    fi
  fi
  echo "[dev] starting frontend (npm start)"
  run_prefixed "[frontend]" "$FRONTEND_LOG" npm start
)

BACKEND_ONLY=${BACKEND_ONLY:-0}
FRONTEND_ONLY=${FRONTEND_ONLY:-0}

if [ "$BACKEND_ONLY" = "1" ]; then
  start_backend
elif [ "$FRONTEND_ONLY" = "1" ]; then
  start_frontend
else
  start_backend &
  BACKEND_PID=$!
  start_frontend &
  FRONTEND_PID=$!
  trap 'echo "[dev] stopping..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' INT TERM
  wait
fi
