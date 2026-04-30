import json
import os
from time import time
from dotenv import load_dotenv
from transformers import pipeline, AutoTokenizer
from kafka import KafkaConsumer, KafkaProducer

load_dotenv()

# ====== CONFIG ======
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_PROCESSED", "processed_comments")
OUTPUT_TOPIC = os.getenv("KAFKA_TOPIC_OUTPUT", "final_comments")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
GROUP_ID = os.getenv("KAFKA_GROUP_MODEL", "roberta-sentiment-group")
BATCH_SIZE = int(os.getenv("MODEL_BATCH_SIZE", 16))
FLUSH_INTERVAL = int(os.getenv("MODEL_FLUSH_INTERVAL", 2))

last_flush = time()

MODEL_NAME = os.getenv("MODEL_NAME", "cardiffnlp/twitter-roberta-base-sentiment")
MODEL_VERSION = os.getenv("MODEL_VERSION", "1.0")

# ====== LOAD MODEL ======
# Load tokenizer riêng để kiểm soát tốt hơn
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

classifier = pipeline(
    "sentiment-analysis",
    model=MODEL_NAME,
    tokenizer=tokenizer,
    truncation=True,        # Kích hoạt cắt tỉa
    max_length=512          # Giới hạn tối đa của RoBERTa
)

label_map = {
    "LABEL_0": "NEGATIVE",
    "LABEL_1": "NEUTRAL",
    "LABEL_2": "POSITIVE"
}

# ====== KAFKA ======
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    group_id=GROUP_ID,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda x: json.dumps(x).encode("utf-8")
)

print("🚀 Sentiment consumer started...")

buffer = []
meta_buffer = []  # giữ metadata (id, timestamp...)

# ====== PROCESS ======
def process_batch(texts):
    results = classifier(texts)

    mapped = []
    for r in results:
        mapped.append({
            "label": label_map[r["label"]],
            "score": float(r["score"])
        })

    return mapped

# ====== MAIN LOOP ======
for message in consumer:
    try:
        data = message.value

        # ====== PARSE INPUT ======
        if isinstance(data, str):
            text = data
            msg_id = None
            ts = int(time())
        elif isinstance(data, dict):
            text = data.get("textComment", "") # get text từ trường "textComment", nếu không có thì mặc định là chuỗi rỗng
            msg_id = data.get("id", None)
            ts = data.get("timestamp", int(time()))
        else:
            text = ""
            msg_id = None
            ts = int(time())

        if text:
            buffer.append(text)
            meta_buffer.append({
                "id": msg_id,
                "timestamp": ts,
                "text": text
            })

        # ====== FLUSH ======
        if len(buffer) >= BATCH_SIZE or ((time() - last_flush) >= FLUSH_INTERVAL and buffer):
            start_time = time()
            results = process_batch(buffer)
            latency = int((time() - start_time) * 1000)

            # ====== BUILD OUTPUT SCHEMA ======
            for i, res in enumerate(results):
                output = {
                    "id": meta_buffer[i]["id"],
                    "text": meta_buffer[i]["text"],
                    "timestamp": meta_buffer[i]["timestamp"],

                    "sentiment": {
                        "label": res["label"],
                        "score": res["score"]
                    },

                    "model": {
                        "name": MODEL_NAME,
                        "version": MODEL_VERSION
                    },

                    "processing_time_ms": latency
                }

                # ====== SEND TO KAFKA ======
                producer.send(OUTPUT_TOPIC, output)

                # debug
                print(json.dumps(output, indent=2))
                print("-" * 60)

            producer.flush()

            buffer.clear()
            meta_buffer.clear()
            last_flush = time()

    except Exception as e:
        print(f"Error: {e}")
