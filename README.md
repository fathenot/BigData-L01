# Real-time Sentiment Analysis Data Pipeline

Hệ thống xử lý luồng dữ liệu thời gian thực, phân tích cảm xúc (Sentiment Analysis) từ các đánh giá sản phẩm Amazon. Sử dụng Apache Kafka, Apache Flink, RoBERTa ML model, PostgreSQL và Dashboard React.

## Kiến trúc hệ thống

```
data.py  (đọc file CSV/JSON từ raw_data/)
   │
   ▼
producer.py  ──►  Kafka: social_media_stream
                        │
                        ▼
              Flink (Main.java / Pipeline.jar)
              [Làm sạch text: xóa URL, @mention, #hashtag]
                        │
                        ▼
                Kafka: processed_comments
                        │
                        ▼
              model.py  (RoBERTa sentiment analysis)
              [Phân loại: POSITIVE / NEUTRAL / NEGATIVE]
                        │
                        ▼
                Kafka: final_comments
                        │
                        ▼
              worker.py  ──►  PostgreSQL
                                   │
                                   ▼
                          BFF (Express :3001)
                                   │
                                   ▼
                       Dashboard (React :5173)
```

---

## Yêu cầu hệ thống

- **Docker & Docker Compose** — chạy Kafka, Zookeeper, Flink, PostgreSQL
- **Java 11** — chỉ cần nếu muốn build lại JAR (không bắt buộc, đã có sẵn `jobs/Pipeline.jar`)
- **Python 3.8+** — chạy Producer, Model, Worker
- **Node.js 18+ (native WSL/Linux)** — chạy BFF và Frontend

> **Lưu ý WSL:** Cài Node.js bằng `nvm` bên trong WSL, không dùng Node.js từ Windows.
> ```bash
> curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
> source ~/.bashrc && nvm install --lts
> ```

---

## Cấu trúc thư mục

```
BigData-L01/
├── src/main/java/org/example/   # Apache Flink (Java)
├── data_ingestion/              # Python: Producer, Worker, API
│   ├── producer.py              # Đọc raw_data/ → Kafka
│   ├── worker.py                # Kafka(final_comments) → PostgreSQL
│   ├── api_server.py            # FastAPI (port 8000)
│   ├── data.py                  # Đọc & multiplex CSV/JSON
│   └── raw_data/                # File dữ liệu thô (gitignored)
├── model/
│   └── model.py                 # RoBERTa sentiment → Kafka
├── bff/                         # Express.js BFF (port 3001)
│   ├── index.js
│   ├── db.js
│   └── routes/                  # products, overview, trend, reviews
├── frontend/                    # React + Vite Dashboard (port 5173)
│   └── src/
│       ├── App.jsx
│       ├── api/index.js
│       └── components/          # FilterBar, OverviewCards, Charts, Table
├── database/
│   └── schema.sql               # 5 bảng PostgreSQL + MLModel seed
├── jobs/
│   └── Pipeline.jar             # Flink JAR đã build sẵn
├── start-demo.sh                # Khởi động toàn bộ pipeline (1 lệnh)
├── stop-demo.sh                 # Dừng toàn bộ pipeline
├── docker-compose.yml
└── .env                         # Config (gitignored, copy từ .env.example)
```

---

## Thiết lập lần đầu (chỉ làm 1 lần)

### Bước 1 — Cấu hình môi trường

```bash
cp .env.example .env
```

Chỉnh `.env` theo cấu hình local của bạn (DB host, port, user, password).

---

### Bước 2 — Chuẩn bị dữ liệu thô

Tạo thư mục `data_ingestion/raw_data/` và đặt file dữ liệu vào đó:

```bash
mkdir -p data_ingestion/raw_data
```

Tải file dữ liệu mẫu tại: **[Google Drive — raw_data] https://drive.google.com/drive/folders/1ASzpnoZ9jXJdFggc8KV0TPzU-dqvUrXi**

Copy toàn bộ file vào `data_ingestion/raw_data/`. Thư mục này bị gitignore nên không được commit.

File được hỗ trợ: `Cell_Phones_and_Accessories_5.json`, `sentiment140.csv`, `train.csv`, `amazon_reviews.csv`.

---

### Bước 3 — Khởi tạo Database

```bash
docker-compose up -d
psql -h localhost -p 5433 -U postgres -d postgres -f database/schema.sql
```

Script tạo 5 bảng và seed row bắt buộc cho bảng `MLModel`.

---

### Bước 4 — Thiết lập Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r data_ingestion/requirements.txt
pip install kafka-python transformers torch fastapi uvicorn pydantic
```

---

### Bước 5 — Cài Node.js dependencies

```bash
cd bff && npm install && cd ..
cd frontend && npm install && cd ..
```

---

## Chạy demo (sau khi đã thiết lập)

### Cách 1 — Script tự động (khuyến nghị)

> **Quan trọng — làm trước khi chạy script để tránh timeout:**
>
> 1. Khởi động Docker infrastructure:
>    ```bash
>    docker-compose up -d
>    ```
> 2. Submit Flink job: mở `http://localhost:8081` → **Submit New Job** → upload `jobs/Pipeline.jar` → Submit
> 3. Chờ Flink job chuyển sang trạng thái **RUNNING**
>
> Lý do: `start-demo.sh` sẽ reset Kafka và xoá toàn bộ topic cũ. Nếu Flink đang chạy và topic bị xoá,
> Flink sẽ báo lỗi `UnknownTopicOrPartitionException`. Script sẽ tự tạo lại topic sau khi reset,
> nhưng Flink job cần được submit **sau** khi script hoàn tất (xem Bước 5/5 trong output của script).

Sau khi Flink job đang RUNNING, chạy:

```bash
./start-demo.sh
```

Script sẽ tự động:
- Khởi động toàn bộ Docker infrastructure
- Reset Kafka (xoá volume cũ, tạo lại topic)
- Xoá dữ liệu cũ trong PostgreSQL
- Khởi động BFF, Frontend, Worker, Model, Producer

Khi script hoàn tất, **submit lại Flink job** nếu chưa có job đang chạy:
- Mở `http://localhost:8081` → Submit New Job → upload `jobs/Pipeline.jar` → Submit

Dừng toàn bộ:

```bash
./stop-demo.sh
```

---

### Cách 2 — Chạy thủ công (từng terminal)

#### Bước 1 — Khởi động hạ tầng

```bash
docker-compose up -d
```

| Service | Port |
|---------|------|
| Zookeeper | 2181 |
| Kafka | 29092 (host) |
| Flink JobManager | 8081 |
| PostgreSQL | 5433 |

#### Bước 2 — Submit Flink Job

Mở `http://localhost:8081` → **Submit New Job** → upload `jobs/Pipeline.jar` → Submit.

> Rebuild JAR sau khi sửa Java code:
> ```bash
> ./gradlew shadowJar
> # Output: build/libs/BigData-L01-1.0-SNAPSHOT-all.jar
> ```

#### Bước 3 — Chạy pipeline Python

Mở 3 terminal, mỗi terminal kích hoạt `venv`:

```bash
# Terminal 1 — Model (chạy trước, đợi tải model ~500MB lần đầu)
source venv/bin/activate
python model/model.py

# Terminal 2 — Worker
source venv/bin/activate
python data_ingestion/worker.py

# Terminal 3 — Producer (sau khi model đã in "consumer started")
source venv/bin/activate
python data_ingestion/producer.py
```

#### Bước 4 — Khởi động BFF và Dashboard

```bash
# Terminal 4
node bff/index.js

# Terminal 5
cd frontend && npm run dev
```

Mở `http://localhost:5173` để xem Dashboard.

---

## Dashboard

| Tính năng | Mô tả |
|-----------|-------|
| Filter ngày | Hôm nay / 3 ngày / 1 tuần / 1 tháng |
| Filter sản phẩm | Dropdown chọn ASIN |
| Overview cards | Total Reviews, Avg Confidence, % Positive/Negative |
| Pie chart | Phân bổ 3 nhãn sentiment |
| Bar chart | Xu hướng review theo ngày |
| Review Table | Bảng chi tiết, click để xem full text |
| Filter tiêu cực | Toggle chỉ xem các review Negative |
| Auto-refresh | Toàn bộ dashboard tự cập nhật mỗi 5 giây |

---

## Xử lý lỗi thường gặp

### Flink: `UnknownTopicOrPartitionException`

Kafka topic bị xoá (do reset volume) trước khi Flink job được submit lại.

**Cách fix:** Tạo lại topic thủ công:

```bash
KAFKA_CONTAINER=$(docker ps --format "{{.Names}}" | grep kafka | grep -v zookeeper | head -1)

for topic in social_media_stream processed_comments final_comments sentiment-input; do
  docker exec "$KAFKA_CONTAINER" kafka-topics \
    --bootstrap-server localhost:9092 --create \
    --topic "$topic" --partitions 3 --replication-factor 1 2>/dev/null \
    && echo "Created: $topic" || echo "Already exists: $topic"
done
```

Sau đó submit lại Flink job tại `http://localhost:8081`.

---

### Kafka: `No resolvable bootstrap urls`

- Đảm bảo Docker đang chạy
- `.env`: `KAFKA_BOOTSTRAP_SERVERS=localhost:29092`
- macOS: dùng `127.0.0.1:29092`

---

### Database: FK violation khi insert SentimentResult

Bảng `MLModel` chưa có seed row. Chạy:

```sql
INSERT INTO public.mlmodel (model_version_id, algorithm_name)
VALUES ('svm-v1.0', 'RoBERTa (cardiffnlp/twitter-roberta-base-sentiment)')
ON CONFLICT DO NOTHING;
```

---

### npm install lỗi UNC path (WSL)

Node.js đang chạy từ Windows. Cài Node.js native trong WSL bằng `nvm` (xem Yêu cầu hệ thống).
