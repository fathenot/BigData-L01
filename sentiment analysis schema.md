# Sentiment Analysis Output Schema

## Overview
Schema này định nghĩa cấu trúc dữ liệu đầu ra của pipeline xử lý sentiment analysis.
Dữ liệu bao gồm nội dung gốc, kết quả phân tích và metadata phục vụ debug và monitoring.

---

## JSON Schema

{
  "id": "uuid",
  "text": "...",
  "sentiment": "positive | neutral | negative",
  "score": 0.92,
  "event_time": "...",
  "processed_time": "...",
  "source": "kafka-topic-name"
}

---

## Field Definitions

### 1. id
- Type: string (UUID)
- Description: Định danh duy nhất cho mỗi message
- Purpose:
  - Tránh duplicate
  - Trace dữ liệu xuyên suốt pipeline

Example:
"id": "550e8400-e29b-41d4-a716-446655440000"

---

### 2. text
- Type: string
- Description: Nội dung văn bản gốc (input của model)
- Purpose:
  - Debug
  - Reprocess khi model thay đổi

Example:
"text": "Sản phẩm này rất tốt"

---

### 3. sentiment
- Type: enum (string)
- Values:
  - positive
  - neutral
  - negative
- Description: Kết quả phân loại cảm xúc từ model
- Purpose:
  - Phân tích dữ liệu
  - Dashboard / báo cáo

Example:
"sentiment": "positive"

---

### 4. score
- Type: float (0 → 1)
- Description: Độ tin cậy của model (confidence score)
- Purpose:
  - Lọc kết quả yếu
  - Đánh giá chất lượng model

Example:
"score": 0.92

---

### 5. event_time
- Type: timestamp (ISO 8601)
- Description: Thời điểm data được tạo (từ producer)
- Purpose:
  - Phân tích theo thời gian
  - Dùng cho window processing

Example:
"event_time": "2026-03-27T14:00:00Z"

---

### 6. processed_time
- Type: timestamp (ISO 8601)
- Description: Thời điểm pipeline xử lý xong
- Purpose:
  - Đo latency (processed_time - event_time)
  - Monitoring hệ thống

Example:
"processed_time": "2026-03-27T14:00:05Z"

---

### 7. source
- Type: string
- Description: Tên Kafka topic chứa dữ liệu gốc
- Purpose:
  - Trace nguồn dữ liệu
  - Debug trong hệ multi-topic

Example:
"source": "raw-text-topic"

---

## Design Principles

### 1. Lưu cả input và output
Không chỉ lưu kết quả sentiment, mà cần lưu cả text gốc để:
- Debug
- Reprocess khi model thay đổi

---

### 2. Phân biệt event_time và processed_time
- event_time: thời điểm data được tạo
- processed_time: thời điểm xử lý

=> Giúp đo latency và phát hiện delay trong pipeline

---

### 3. score không tuyệt đối
- score là confidence, không phải đảm bảo đúng 100%
- Có thể dùng threshold để lọc kết quả

---

## Summary

- id: định danh duy nhất
- text: nội dung gốc
- sentiment: kết quả phân loại
- score: độ tin cậy
- event_time: thời điểm data được tạo
- processed_time: thời điểm xử lý
- source: Kafka topic nguồn
