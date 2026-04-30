import os
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="Sentiment Analytics API")

# Cho phép Dashboard (Frontend) truy cập
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "sentiment_db"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", "abc"),
}

@app.get("/analytics/product-sentiment")
def get_product_sentiment():
    """Truy vấn kết hợp giữa bảng SentimentResult, AmazonReview và Product"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Câu lệnh SQL Join 3 bảng để lấy thống kê
    query = """
        SELECT p.product_name, sr.sentiment_label, COUNT(*)
        FROM SentimentResult sr
        JOIN AmazonReview ar ON sr.review_id = ar.review_id
        JOIN Product p ON ar.product_id = p.product_id
        GROUP BY p.product_name, sr.sentiment_label;
    """
    cur.execute(query)
    rows = cur.fetchall()

    # Định dạng lại dữ liệu để Frontend dễ vẽ biểu đồ
    results = {}
    for row in rows:
        p_name, label, count = row
        if p_name not in results:
            results[p_name] = {"positive": 0, "negative": 0}
        results[p_name][label.lower()] = count

    cur.close()
    conn.close()
    return results

@app.get("/health")
def health_check():
    return {"status": "online", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"), port=int(os.getenv("API_PORT", 8000)))
