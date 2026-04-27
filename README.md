# 🚀 Real-time Sentiment Analysis Data Pipeline

Dự án Xử lý dữ liệu lớn (Big Data) thời gian thực nhằm phân tích cảm xúc (Sentiment Analysis) từ các bình luận trên mạng xã hội/đánh giá sản phẩm. Hệ thống sử dụng kiến trúc luồng (Streaming Architecture) để tiếp nhận, xử lý, lưu trữ và cung cấp dữ liệu cho Dashboard theo thời gian thực.

## 🏗 Kiến trúc Hệ thống (Data Flow)
`Producer (Python)` ➡️ `Kafka (Raw Topic)` ➡️ `Apache Flink (Java)` ➡️ `Kafka (Processed Topic)` ➡️ `Worker (Python)` ➡️ `PostgreSQL` ➡️ `FastAPI` ➡️ `Dashboard`

1. **Kafka (Ingestion):** Nhận dữ liệu bình luận thô.
2. **Apache Flink (Processing):** Làm sạch văn bản (Clean text), bóc tách dữ liệu và phân tích cảm xúc (Sử dụng ML Model giả lập).
3. **Kafka (Buffer):** Chứa dữ liệu đã được Flink xử lý.
4. **Python Worker (Storage):** Lắng nghe Kafka và Upsert dữ liệu vào 5 bảng chuẩn hóa trong PostgreSQL.
5. **FastAPI (Serving):** Cung cấp API truy vấn dữ liệu từ DB cho Frontend Dashboard.

---

## 📁 Cấu trúc thư mục

```text
BigData-L01/
├── src/main/java/org/example/          # Tầng xử lý luồng (Apache Flink - Java)
├── data_ingestion/                     # Tầng kết nối & API (Python)
│   ├── producer.py                     # Script tạo dữ liệu giả lập đẩy vào Kafka
│   ├── worker.py                       # Script đọc Kafka lưu vào Database
│   ├── api_server.py                   # FastAPI Server phục vụ Dashboard
│   └── requirements.txt                # Thư viện Python
├── sql/                                # Tầng Database
│   └── schema.sql                      # Script tạo 5 bảng chuẩn hóa PostgreSQL
├── docker-compose.yml                  # Cấu hình hạ tầng (Kafka, Zookeeper, Postgres, Flink)
├── build.gradle                        # Cấu hình build dự án Java
└── README.md                           # Tài liệu hướng dẫn
```

---

## 💻 Yêu cầu hệ thống (Prerequisites)
- **Docker & Docker Compose** (Để chạy Kafka, Zookeeper, Postgres, Flink Cluster)
- **Java 11** (Để chạy và build code Apache Flink)
- **Python 3.8+** (Để chạy Worker, Producer, API)
- **DBeaver** (Khuyên dùng - Để quản lý và xem dữ liệu PostgreSQL)

---

## 🚀 Hướng dẫn chạy dự án (Từng bước)

### Bước 1: Khởi động Hạ tầng (Infrastructure)
Mở Terminal tại thư mục gốc của dự án và chạy:
```bash
docker-compose up -d
```
*Hệ thống sẽ khởi động: Zookeeper (2181), Kafka (9092/29092), PostgreSQL (5432/5433), Flink JobManager (8081).*

### Bước 2: Khởi tạo Cơ sở dữ liệu (PostgreSQL)
1. Sử dụng DBeaver kết nối vào PostgreSQL qua `127.0.0.1:5432` (User: `admin`, Pass: `password`).
2. Mở file `sql/schema.sql` và chạy toàn bộ Script để tạo 5 bảng (`StreamTopic`, `Product`, `AmazonReview`, `MLModel`, `SentimentResult`).

### Bước 3: Chạy Apache Flink Job (Xử lý luồng)
Hệ thống Flink sẽ tạo Topic Kafka và bắt đầu lắng nghe luồng dữ liệu. Chạy lệnh sau:
```bash
./gradlew clean run
```
*(Nếu thành công, terminal sẽ dừng ở mức `80% EXECUTING` và không báo lỗi. Điều này là bình thường vì Flink đang chạy ngầm 24/7 chờ dữ liệu).*

### Bước 4: Thiết lập Môi trường Python
Mở một Terminal **mới** (giữ nguyên Terminal của Flink), tạo môi trường ảo để không xung đột với máy thật:
```bash
# Tạo môi trường ảo
python3 -m venv venv

# Kích hoạt môi trường ảo (Mac/Linux)
source venv/bin/activate
# (Nếu dùng Windows: venv\Scripts\activate)

# Cài đặt thư viện
pip install -r data_ingestion/requirements.txt
pip install fastapi uvicorn psycopg2-binary pydantic python-dotenv
```

### Bước 5: Khởi chạy Python Worker & API Server
Vẫn trong môi trường ảo `(venv)`, mở các Terminal mới để chạy song song:

**Khởi chạy Worker (Lưu Database):**
```bash
python data_ingestion/worker.py
```
**Khởi chạy API Server:**
```bash
python data_ingestion/api_server.py
```
*(API sẽ chạy tại `http://localhost:8000/docs` để bạn test dữ liệu).*

### Bước 6: Bơm dữ liệu (Test Pipeline)
Mở thêm một Terminal mới (nhớ active `venv`), chạy file Producer để tạo dữ liệu giả lập đẩy vào hệ thống:
```bash
python data_ingestion/producer.py
```
👉 **Quan sát kết quả:** Dữ liệu từ Producer sinh ra $\rightarrow$ Chảy qua màn hình log của Flink $\rightarrow$ Chảy qua log của Python Worker $\rightarrow$ Mở DBeaver sẽ thấy dữ liệu xuất hiện trong Database!

---

## ⚠️ Lưu ý quan trọng & Khắc phục lỗi (Đặc biệt cho macOS)

### 1. Lỗi mạng (Timeout) / Không tìm thấy Kafka
**Hiện tượng:** `No resolvable bootstrap urls` hoặc `Timed out waiting for a node assignment`.
**Nguyên nhân:** Do macOS đôi khi nhầm lẫn giữa `localhost` (IPv6) và Docker (IPv4).
**Cách khắc phục:** - Tuyệt đối KHÔNG dùng chữ `kafka` hay `localhost` khi chạy code ở máy host.
- Trong `Main.java`, `worker.py` và `docker-compose.yml`, hãy đảm bảo sử dụng chính xác IP số: **`127.0.0.1:29092`** cho Kafka và **`127.0.0.1:5432`** cho PostgreSQL.

### 2. Lỗi "Bóng ma" Kafka (Cache Volume)
**Hiện tượng:** Đã cấu hình đúng IP nhưng Flink vẫn không tạo được Topic.
**Nguyên nhân:** Kafka lưu cấu hình cũ bị lỗi trong ổ cứng ảo của Docker.
**Cách khắc phục (Reset Factory):**
```bash
docker-compose down -v  # Cờ -v sẽ xóa sạch ổ cứng lưu trữ của Kafka
docker-compose up -d
```
---

## 📦 Triển khai (Deployment lên Flink Dashboard)
Nếu không muốn chạy lệnh terminal `./gradlew clean run` nữa mà muốn nộp Job lên web UI chuẩn chỉnh:
1. Port trong `Main.java`: Có 3 vị trí port: chỉnh thành `127.0.0.1:29092` để test bug local trên máy. Chuyển thành cổng nội bộ `kafka:9092` khi build JAR để ném lên flink.
2. Đóng gói dự án:
   ```bash
   ./gradlew clean shadowJar
   ```
3. Lấy file Fat-JAR tại `build/libs/FlinkProject-1.0-SNAPSHOT-all.jar`.
4. Mở `http://localhost:8081` (Flink Dashboard) $\rightarrow$ Submit New Job $\rightarrow$ Upload file JAR và chạy.
```