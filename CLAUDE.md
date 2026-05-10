# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Start all infrastructure (Kafka, Zookeeper, Flink, PostgreSQL)
docker-compose up -d

# Build fat JAR for Flink deployment (uses kafka:9092 internally)
./gradlew shadowJar
# Output: build/libs/BigData-L01-1.0-SNAPSHOT-all.jar

# Run Flink job locally via Gradle (blocks at ~80% EXECUTING — normal, Flink is waiting for data)
./gradlew clean run

# Python deps (run from project root)
pip install -r data_ingestion/requirements.txt

# Run each pipeline component (each in its own terminal, with venv active)
python data_ingestion/producer.py   # ingest raw data → Kafka
python data_ingestion/worker.py     # Kafka → PostgreSQL
python data_ingestion/api_server.py # FastAPI at http://localhost:8000/docs
python model/model.py               # Kafka → RoBERTa sentiment → Kafka
```

## Architecture

**Full data flow:**
```
data.py (raw_data/ files)
  → producer.py → Kafka: social_media_stream
    → Flink (Main.java): text cleaning (strip URLs, @mentions, #hashtags)
      → Kafka: processed_comments
        → model.py: RoBERTa sentiment analysis
          → Kafka: final_comments
            → worker.py → PostgreSQL (5 tables)
```

**Two Kafka addresses:**
- `kafka:9092` — Docker-internal, used by Flink (JAR running inside Docker network)
- `localhost:29092` — host access, used by all Python scripts

**Config:** All environment config is in `.env` (root). Python files use `load_dotenv()` + `os.getenv()`. Java uses `System.getenv().getOrDefault()`. `.env.example` documents all keys without secrets.

**Java model (`SocialMediaComment`):** Fields: `timestamp` (long), `textComment` (String), `topic` (String), `label` (int). No `id` field — Flink does not assign UUIDs.

**Database schema** (`database/schema.sql`): 5 tables — `StreamTopic`, `Product`, `AmazonReview`, `MLModel`, `SentimentResult`. `SentimentResult.model_version_id` is a FK to `MLModel` — that table must have a seed row before worker.py can insert.

**Flink deployment:** A pre-compiled JAR is at `jobs/Pipeline.jar`. Submit via Flink Dashboard at `http://localhost:8081` → Submit New Job. Rebuild with `./gradlew shadowJar` after any Java changes.

**Raw data files** live in `data_ingestion/raw_data/`. `data.py` multiplexes multiple CSV/JSON formats defined in `FILE_CONFIGS` and yields records round-robin randomly. Only `Cell_Phones_and_Accessories_5.json` is committed; other files (`sentiment140.csv`, `train.csv`, `amazon_reviews.csv`) must be added manually.
