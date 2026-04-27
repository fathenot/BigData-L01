import json
import psycopg2
from confluent_kafka import Consumer

# Cấu hình kết nối
DB_CONFIG = {
    "host": "localhost", # Do kết nối từ máy ngoài vào docker
    "database": "sentiment_db",
    "user": "admin",
    "password": "abc"
}

KAFKA_CONFIG = {
    'bootstrap.servers': 'localhost:29092',
    'group.id': 'python-db-writer-group',
    'auto.offset.reset': 'earliest'
}

def insert_to_db(conn, data):
    with conn.cursor() as cur:
        # 1. Insert StreamTopic (Lấy UUID trả về)
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
        """, (data['id'], topic_id, asin, data['text'], data.get('star_rating', 0), data['event_time']))

        # 4. Insert SentimentResult
        cur.execute("""
            INSERT INTO SentimentResult (review_id, model_version_id, sentiment_label, confidence_score, processed_time)
            VALUES (%s, %s, %s, %s, %s);
        """, (data['id'], 'svm-v1.0', data['sentiment'], data['score'], data['processed_time']))
        
    conn.commit()
    print(f"✅ Đã lưu review {data['id']} vào Database.")

if __name__ == '__main__':
    conn = psycopg2.connect(**DB_CONFIG)
    consumer = Consumer(KAFKA_CONFIG)
    # Lắng nghe đúng topic Flink đẩy ra
    consumer.subscribe(['processed_comments']) 
    
    print("Đang lắng nghe Kafka...")
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None: continue
            if msg.error():
                print(f"Kafka Error: {msg.error()}")
                continue
            
            try:
                # Đọc chuỗi JSON phẳng và ghi xuống nhiều bảng
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