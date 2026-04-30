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
- **DBeaver** hoặc `psql` — để khởi tạo schema

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
├── docker-compose.yml
└── .env                         # Config (gitignored, copy từ .env.example)
```

---

## Hướng dẫn chạy

### Bước 1 — Cấu hình môi trường

```bash
cp .env.example .env
```

Chỉnh `.env` theo cấu hình local của bạn (DB host, port, user, password).

---

### Bước 2 — Khởi động hạ tầng

```bash
docker-compose up -d
```

| Service | Port |
|---------|------|
| Zookeeper | 2181 |
| Kafka | 29092 (host) |
| Flink JobManager | 8081 |
| PostgreSQL | 5433 |

---

### Bước 3 — Khởi tạo Database

```bash
psql -h localhost -p 5433 -U postgres -d postgres -f database/schema.sql
```

Script tạo 5 bảng và thêm seed row bắt buộc cho bảng `MLModel`.

---

### Bước 4 — Thiết lập Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r data_ingestion/requirements.txt
pip install kafka-python transformers torch fastapi uvicorn pydantic
```

---

### Bước 5 — Submit Flink Job

Mở `http://localhost:8081` → **Submit New Job** → upload `jobs/Pipeline.jar` → Submit.

Flink tự tạo các Kafka topic cần thiết và lắng nghe data.

> Rebuild JAR sau khi sửa Java code:
> ```bash
> ./gradlew shadowJar
> # Output: build/libs/BigData-L01-1.0-SNAPSHOT-all.jar
> ```

---

### Bước 6 — Chạy pipeline Python

Mở 3 terminal riêng, mỗi terminal kích hoạt `venv`:

```bash
# Terminal 1 — Model (chạy trước, đợi tải model ~500MB lần đầu)
python model/model.py

# Terminal 2 — Worker
python data_ingestion/worker.py

# Terminal 3 — Producer (sau khi model đã ready)
python data_ingestion/producer.py
```

---

### Bước 7 — Khởi động BFF và Dashboard

```bash
# Terminal 4 — BFF (Express)
cd bff
npm install      # lần đầu
node index.js    # chạy tại localhost:3001

# Terminal 5 — Frontend (React)
cd frontend
npm install      # lần đầu
npm run dev      # chạy tại localhost:5173
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
| Auto-refresh | Bảng tự cập nhật mỗi 10 giây |

---

## Xử lý lỗi thường gặp

### Kafka: `No resolvable bootstrap urls`
- Đảm bảo Docker đang chạy
- `.env`: `KAFKA_BOOTSTRAP_SERVERS=localhost:29092`
- macOS: dùng `127.0.0.1:29092`

### Kafka: topic lỗi / cache cũ
```bash
docker-compose down -v && docker-compose up -d
```

### Database: FK violation khi insert SentimentResult
```sql
INSERT INTO public.mlmodel (model_version_id, algorithm_name)
VALUES ('svm-v1.0', 'RoBERTa (cardiffnlp/twitter-roberta-base-sentiment)')
ON CONFLICT DO NOTHING;
```

### npm install lỗi UNC path (WSL)
Node.js đang chạy từ Windows. Cài Node.js native trong WSL bằng `nvm` (xem Yêu cầu hệ thống).
