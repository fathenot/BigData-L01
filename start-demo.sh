#!/bin/bash
set -e

# ── Colours ──────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
step()    { echo -e "\n${BOLD}$*${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Load .env ─────────────────────────────────────────────
if [ ! -f .env ]; then
  echo -e "${RED}[ERROR]${NC} File .env không tồn tại. Hãy copy từ .env.example trước."; exit 1
fi
set -a; source .env; set +a

# ── Bước 0: Đảm bảo toàn bộ Docker infrastructure đang chạy ─
step "▶ Bước 0 — Khởi động Docker infrastructure (Postgres, Flink, Kafka...)"
docker-compose up -d
info "Chờ các service khởi động..."
sleep 5
success "Docker infrastructure đang chạy"

# ── Bước 1/5: Reset Docker — xoá Kafka data, giữ Postgres ─
step "▶ Bước 1/5 — Reset Kafka (xoá volume cũ)"

# Chỉ dừng Kafka + Zookeeper, giữ nguyên Flink và Postgres
info "Dừng Kafka và Zookeeper..."
docker-compose stop kafka zookeeper 2>/dev/null || true

# Xoá Kafka volume để bắt đầu hoàn toàn sạch
KAFKA_VOL=$(docker volume ls --format "{{.Name}}" | grep "kafka-data" | head -1)
if [ -n "$KAFKA_VOL" ]; then
  docker volume rm "$KAFKA_VOL" && info "Đã xoá Kafka volume: $KAFKA_VOL"
else
  info "Kafka volume chưa tồn tại (bỏ qua)"
fi

# Khởi động lại chỉ Kafka + Zookeeper (Flink và Postgres vẫn chạy)
info "Khởi động lại Kafka và Zookeeper..."
docker-compose up -d kafka zookeeper
success "Kafka khởi động lại với volume mới hoàn toàn"

TIMEOUT=60; ELAPSED=0

# Chờ PostgreSQL
info "Đang chờ PostgreSQL sẵn sàng..."
until PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q; do
  sleep 2; ELAPSED=$((ELAPSED + 2))
  if [ $ELAPSED -ge $TIMEOUT ]; then
    echo -e "${RED}[ERROR]${NC} PostgreSQL không phản hồi sau ${TIMEOUT}s."; exit 1
  fi
done
success "PostgreSQL ready (${ELAPSED}s)"

# Chờ Kafka
info "Đang chờ Kafka sẵn sàng..."
ELAPSED=0
until docker ps --filter "name=kafka" --filter "status=running" --format "{{.Names}}" \
      | grep -qv zookeeper 2>/dev/null; do
  sleep 2; ELAPSED=$((ELAPSED + 2))
  if [ $ELAPSED -ge $TIMEOUT ]; then
    warn "Kafka chưa ready sau ${TIMEOUT}s — tiếp tục anyway"; break
  fi
done
sleep 5
success "Kafka ready"

# Tạo Kafka topics trước khi submit Flink job
info "Tạo Kafka topics..."
KAFKA_CONTAINER=$(docker ps --filter "name=kafka" --format "{{.Names}}" | grep -v zookeeper | head -1)
for topic in social_media_stream processed_comments final_comments sentiment-input; do
  docker exec "$KAFKA_CONTAINER" kafka-topics \
    --bootstrap-server localhost:9092 --create \
    --topic "$topic" --partitions 3 --replication-factor 1 2>/dev/null \
    && info "  Created: $topic" || info "  Already exists: $topic"
done
success "Kafka topics sẵn sàng — có thể submit Flink job ngay"

# ── Bước 2/5: Xoá data cũ trong PostgreSQL ───────────────
step "▶ Bước 2/5 — Xoá dữ liệu cũ trong PostgreSQL"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<SQL
TRUNCATE sentimentresult, amazonreview, product, streamtopic RESTART IDENTITY CASCADE;
SQL
success "Đã truncate 4 bảng (giữ nguyên MLModel seed)"

# ── Bước 3/5: Khởi động BFF + Frontend ───────────────────
step "▶ Bước 3/5 — Khởi động BFF và Frontend"
mkdir -p logs
rm -f .demo.pids

info "Khởi động BFF (port ${BFF_PORT:-3001})..."
node bff/index.js > logs/bff.log 2>&1 &
echo $! >> .demo.pids
success "BFF started  →  http://localhost:${BFF_PORT:-3001}"

info "Khởi động Frontend (port 5173)..."
(cd frontend && npm run dev -- --host 0.0.0.0) > logs/frontend.log 2>&1 &
echo $! >> .demo.pids
success "Frontend started  →  http://localhost:5173"

# ── Bước 4/5: Khởi động Python pipeline ──────────────────
step "▶ Bước 4/5 — Khởi động Python pipeline"

if [ -f venv/bin/activate ]; then
  source venv/bin/activate
  info "Đã kích hoạt virtualenv"
else
  warn "Không tìm thấy venv/ — dùng Python system"
fi

info "Khởi động Worker..."
python -u data_ingestion/worker.py > logs/worker.log 2>&1 &
echo $! >> .demo.pids
success "Worker started  →  logs/worker.log"

info "Khởi động Model (RoBERTa)..."
python -u model/model.py > logs/model.log 2>&1 &
MODEL_PID=$!
echo $MODEL_PID >> .demo.pids
success "Model started  →  logs/model.log"

info "Đang chờ model load xong (có thể mất 1-5 phút lần đầu)..."
TIMEOUT=360; ELAPSED=0
while ! grep -q "consumer started" logs/model.log 2>/dev/null; do
  if ! kill -0 "$MODEL_PID" 2>/dev/null; then
    echo -e "${RED}[ERROR]${NC} Model process đã crash. Log cuối:"
    tail -20 logs/model.log
    exit 1
  fi
  sleep 2; ELAPSED=$((ELAPSED + 2))
  if [ $((ELAPSED % 10)) -eq 0 ]; then
    LAST=$(tail -1 logs/model.log 2>/dev/null || echo "(chưa có output)")
    info "  [${ELAPSED}s] $LAST"
  fi
  if [ $ELAPSED -ge $TIMEOUT ]; then
    warn "Model mất quá lâu — khởi động Producer anyway (data sẽ queue trong Kafka)"
    break
  fi
done
grep -q "consumer started" logs/model.log 2>/dev/null && success "Model ready!"

info "Khởi động Producer..."
python -u data_ingestion/producer.py > logs/producer.log 2>&1 &
echo $! >> .demo.pids
success "Producer started  →  logs/producer.log"

# ── Bước 5/5: Nhắc submit Flink job ──────────────────────
step "▶ Bước 5/5 — Submit Flink Job (thủ công)"
echo ""
echo -e "  ${YELLOW}Kafka topics đã sẵn sàng. Hãy submit Flink job:${NC}"
echo -e "  1. Mở ${CYAN}http://localhost:8081${NC}"
echo -e "  2. Submit New Job → upload ${BOLD}jobs/Pipeline.jar${NC} → Submit"
echo ""

# ── Done ──────────────────────────────────────────────────
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║        DEMO ĐANG CHẠY THÀNH CÔNG        ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Dashboard:   ${CYAN}http://localhost:5173${NC}"
echo -e "  BFF API:     ${CYAN}http://localhost:${BFF_PORT:-3001}/health${NC}"
echo -e "  Flink UI:    ${CYAN}http://localhost:8081${NC}"
echo ""
echo -e "  Xem log:     ${YELLOW}tail -f logs/worker.log${NC}"
echo -e "              ${YELLOW}tail -f logs/model.log${NC}"
echo -e "              ${YELLOW}tail -f logs/producer.log${NC}"
echo ""
echo -e "  Dừng tất cả: ${RED}./stop-demo.sh${NC}"
