import json
import time
from kafka import KafkaProducer

from data import stream_multisource_data

producer = KafkaProducer(
    bootstrap_servers=['127.0.0.1:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

TOPIC_NAME = 'social_media_stream'
BATCH_SIZE = 10
SLEEP_TIME = 0.5     

print("🚀 Starting Kafka Producer (Multi-source)...")

sent_count = 0

try:
    for payload in stream_multisource_data():
        
        producer.send(TOPIC_NAME, value=payload)
        sent_count += 1
        
        if sent_count % BATCH_SIZE == 0:
            producer.flush()
            print(f"✅ Upload {sent_count} records... (Wait{SLEEP_TIME}s)")
            time.sleep(SLEEP_TIME)

    producer.flush()
    print("\n🎉 Successfully broadcasted the entire dataset!")

except KeyboardInterrupt:
    print("\n🛑 Broadcast stopped.")
except Exception as e:
    print(f"\n❌ Producer system error: {e}")
finally:
    producer.close()