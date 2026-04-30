# Real-time Sentiment Analysis Data Pipeline

Hệ thống xử lý luồng dữ liệu thời gian thực, phân tích cảm xúc (Sentiment Analysis) từ các đánh giá sản phẩm Amazon. Sử dụng Apache Kafka, Apache Flink, RoBERTa ML model và PostgreSQL.

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
```

---

## Yêu cầu hệ thống

- **Docker & Docker Compose** — chạy Kafka, Zookeeper, Flink, PostgreSQL
- **Java 11** — chỉ cần nếu muốn build lại JAR (không bắt buộc, đã có sẵn `jobs/Pipeline.jar`)
- **Python 3.8+** — chạy Producer, Model, Worker, API
- **DBeaver** hoặc `psql` — để khởi tạo schema và kiểm tra dữ liệu

---

## Hướng dẫn chạy pipeline

### Bước 1 — Cấu hình môi trường

Sao chép file cấu hình mẫu và điền thông tin phù hợp:

```bash
cp .env.example .env
```

Mở `.env` và chỉnh các giá trị nếu cần (mặc định đã hoạt động với `docker-compose.yml`):

```env
DB_HOST=localhost
DB_PORT=5432        # hoặc 5433 nếu port 5432 đã bị chiếm
DB_NAME=sentiment_db
DB_USER=postgres    # hoặc admin — tuỳ cấu hình Docker của bạn
DB_PASSWORD=password
```

---

### Bước 2 — Khởi động hạ tầng

```bash
docker-compose up -d
```

Chờ khoảng 15–20 giây để tất cả service sẵn sàng. Kiểm tra:

```bash
docker-compose ps
```

Tất cả service phải ở trạng thái `Up`:

| Service | Port |
|---------|------|
| Zookeeper | 2181 |
| Kafka | 9092 (Docker nội bộ), 29092 (host) |
| Flink JobManager | 8081 |
| PostgreSQL | 5432 |

---

### Bước 3 — Khởi tạo Database

Dùng DBeaver hoặc `psql` kết nối vào PostgreSQL với thông tin trong `.env`, sau đó chạy:

```bash
# Dùng psql (thay thông tin theo .env)
psql -h localhost -p 5432 -U postgres -d sentiment_db -f database/schema.sql
```

Script sẽ tạo 5 bảng (`StreamTopic`, `Product`, `AmazonReview`, `MLModel`, `SentimentResult`) và thêm seed data bắt buộc cho bảng `MLModel`.

---

### Bước 4 — Thiết lập Python

```bash
# Tạo và kích hoạt môi trường ảo
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Cài thư viện
pip install -r data_ingestion/requirements.txt
pip install kafka-python transformers torch fastapi uvicorn pydantic
```

---

### Bước 5 — Submit Flink Job

Mở trình duyệt tại **http://localhost:8081** (Flink Dashboard):

1. Chọn **Submit New Job** → **+ Add New**
2. Upload file `jobs/Pipeline.jar`
3. Nhấn **Submit**

Flink sẽ tự động tạo các Kafka topic cần thiết (`social_media_stream`, `processed_comments`, `sentiment-input`) và bắt đầu lắng nghe dữ liệu.

> **Lưu ý:** Nếu muốn build lại JAR sau khi sửa Java code:
> ```bash
> ./gradlew shadowJar
> # Output: build/libs/BigData-L01-1.0-SNAPSHOT-all.jar
> ```

---

### Bước 6 — Khởi chạy Worker (lưu DB)

Mở terminal mới, kích hoạt venv, chạy:

```bash
python data_ingestion/worker.py
```

Worker sẽ lắng nghe topic `final_comments` và ghi kết quả vào PostgreSQL.

---

### Bước 7 — Khởi chạy Model (phân tích sentiment)

Mở terminal mới, kích hoạt venv, chạy:

```bash
python model/model.py
```

Lần đầu chạy sẽ tự tải model RoBERTa (~500MB). Model đọc từ `processed_comments`, phân tích cảm xúc và đẩy kết quả vào `final_comments`.

---

### Bước 8 — Bơm dữ liệu

Mở terminal mới, kích hoạt venv, chạy:

```bash
python data_ingestion/producer.py
```

Producer đọc các file trong `data_ingestion/raw_data/` và đẩy dữ liệu vào Kafka.

> **File dữ liệu có sẵn:** `Cell_Phones_and_Accessories_5.json`
> Producer cũng hỗ trợ: `sentiment140.csv`, `train.csv`, `amazon_reviews.csv` (cần thêm thủ công vào `raw_data/`)

---

### Kiểm tra kết quả

Theo dõi log của từng terminal. Khi pipeline hoạt động đúng:

- **Worker** in: `✅ Saved review abc12345... | positive (0.92)`
- **Model** in: output JSON của từng batch

Kiểm tra dữ liệu trong database:

```sql
SELECT COUNT(*) FROM SentimentResult;
SELECT sentiment_label, COUNT(*) FROM SentimentResult GROUP BY sentiment_label;
```

API endpoint kiểm tra: `http://localhost:8000/analytics/product-sentiment`

---

## Xử lý lỗi thường gặp

### Kafka: `No resolvable bootstrap urls`

Python scripts dùng `localhost:29092`. Nếu gặp lỗi này:
- Đảm bảo Docker đang chạy (`docker-compose ps`)
- Đảm bảo `.env` có `KAFKA_BOOTSTRAP_SERVERS=localhost:29092`
- Trên macOS: dùng `127.0.0.1:29092` thay vì `localhost:29092`

### Kafka: Topic đã tồn tại nhưng Flink vẫn lỗi (Cache Volume)

```bash
docker-compose down -v    # xóa sạch volumes
docker-compose up -d
```

### Database: `FK violation` khi insert SentimentResult

Bảng `MLModel` chưa có seed data. Chạy lại `database/schema.sql` hoặc insert thủ công:

```sql
INSERT INTO public.mlmodel (model_version_id, algorithm_name)
VALUES ('svm-v1.0', 'RoBERTa (cardiffnlp/twitter-roberta-base-sentiment)')
ON CONFLICT DO NOTHING;
```

### Database: Connection refused

Kiểm tra port và credentials trong `.env` khớp với `docker-compose.yml`. PostgreSQL mặc định chạy ở port `5432`.
