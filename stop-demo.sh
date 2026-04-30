#!/bin/bash

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load BFF_PORT từ .env nếu có
[ -f .env ] && { set -a; source .env; set +a; }
BFF_PORT="${BFF_PORT:-3001}"

echo -e "${CYAN}Đang dừng tất cả tiến trình demo...${NC}"

kill_port() {
  local port=$1 name=$2
  if fuser "${port}/tcp" &>/dev/null; then
    fuser -k "${port}/tcp" &>/dev/null
    echo -e "  ${RED}✕${NC} $name (port $port) stopped"
  else
    echo -e "  — $name (port $port) không chạy"
  fi
}

# Kill theo port (đáng tin nhất)
kill_port "$BFF_PORT" "BFF"
kill_port "5173"       "Frontend"

# Kill Python processes theo PID file
if [ -f .demo.pids ]; then
  while read -r pid; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null
      echo -e "  ${RED}✕${NC} Đã dừng PID $pid"
    fi
  done < .demo.pids
  rm -f .demo.pids
fi

# Fallback: kill theo tên process
pkill -f "model/model.py"          2>/dev/null && echo -e "  ${RED}✕${NC} Model stopped"    || true
pkill -f "worker.py"               2>/dev/null && echo -e "  ${RED}✕${NC} Worker stopped"   || true
pkill -f "producer.py"             2>/dev/null && echo -e "  ${RED}✕${NC} Producer stopped" || true

echo -e "\n${GREEN}Tất cả tiến trình đã dừng.${NC}"
