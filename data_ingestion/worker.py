import json
import os
import uuid
from datetime import datetime, timezone
import psycopg2
from dotenv import load_dotenv
from confluent_kafka import Consumer

load_dotenv()

# Cấu hình kết nối
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "sentiment_db"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", "abc"),
}

KAFKA_CONFIG = {
    'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092"),
    'group.id': os.getenv("KAFKA_GROUP_DB_WRITER", "python-db-writer-group"),
    'auto.offset.reset': 'earliest'
}

def insert_to_db(conn, data):
    # data shape (from model.py → final_comments):
    # { id, text, timestamp, sentiment: {label, score}, model: {...}, processing_time_ms }
    review_id = data.get('id') or str(uuid.uuid4())
    sentiment = data.get('sentiment', {})
    sentiment_label = sentiment.get('label', 'NEUTRAL').lower()
    confidence_score = sentiment.get('score', 0.0)
    event_time = datetime.fromtimestamp(data['timestamp'], tz=timezone.utc)
    processed_time = datetime.now(tz=timezone.utc)

    with conn.cursor() as cur:
        # 1. Insert StreamTopic
        cur.execute("""
            INSERT INTO StreamTopic (topic_name) VALUES (%s)
            ON CONFLICT (topic_name) DO UPDATE SET topic_name = EXCLUDED.topic_name
            RETURNING topic_id;
        """, (data.get('source', 'unknown'),))
        topic_id = cur.fetchone()[0]

        # 2. Insert Product
        asin = data.get('product_asin', 'UNKNOWN')
        cur.execute("""
            INSERT INTO Product (product_asin) VALUES (%s)
            ON CONFLICT (product_asin) DO NOTHING;
        """, (asin,))

        # 3. Insert AmazonReview
        cur.execute("""
            INSERT INTO AmazonReview (review_id, topic_id, product_asin, original_text, star_rating, event_time)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (review_id) DO NOTHING;
        """, (review_id, topic_id, asin, data.get('text', ''), data.get('star_rating') or None, event_time))

        # 4. Insert SentimentResult
        cur.execute("""
            INSERT INTO SentimentResult (review_id, model_version_id, sentiment_label, confidence_score, processed_time)
            VALUES (%s, %s, %s, %s, %s);
        """, (review_id, 'svm-v1.0', sentiment_label, confidence_score, processed_time))

    conn.commit()
    print(f"✅ Saved review {review_id[:8]}... | {sentiment_label} ({confidence_score:.2f})")

if __name__ == '__main__':
    conn = psycopg2.connect(**DB_CONFIG)
    consumer = Consumer(KAFKA_CONFIG)
    # Đọc từ final_comments — output của model.py (có sentiment data)
    consumer.subscribe([os.getenv("KAFKA_TOPIC_OUTPUT", "final_comments")])

    print("Đang lắng nghe Kafka topic: final_comments ...")
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None: continue
            if msg.error():
                print(f"Kafka Error: {msg.error()}")
                continue

            try:
                data = json.loads(msg.value().decode('utf-8'))
                insert_to_db(conn, data)
            except Exception as e:
                print(f"Lỗi DB: {e}")
                conn.rollback()

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        conn.close()
        print("Đã đóng kết nối.")
