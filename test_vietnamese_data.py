"""
Kiem tra tich hop dataset tieng Viet vao data.py
Chay: python test_vietnamese_data.py
"""
import sys, os, csv, json

# Fix encoding cho Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

def sep(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

# -------------------------------------------------------------------
# TEST 1: FILE_CONFIGS co du 4 entry tieng Viet
# -------------------------------------------------------------------
sep("TEST 1: FILE_CONFIGS entries")
from data import FILE_CONFIGS, get_file_generator, stream_multisource_data

vi_files = [
    'uit_vsfc.csv',
    'minhtoan_sentiment.csv',
    'polarbear_sentiment.csv',
    'vietnamese_sentiment_combined.csv',
]
all_ok = True
for fname in vi_files:
    cfg = FILE_CONFIGS.get(fname)
    if cfg is None:
        print(f"  {FAIL}  {fname} KHONG CO trong FILE_CONFIGS")
        all_ok = False
        continue
    ok = (
        cfg['format'] == 'csv_with_header' and
        cfg['text_col'] == 'text' and
        cfg['label_col'] == 'label' and
        set(cfg['label_map'].keys()) == {'positive', 'negative', 'neutral'} and
        cfg['label_map']['positive'] == 1 and
        cfg['label_map']['negative'] == 0 and
        cfg['label_map']['neutral'] == 0
    )
    print(f"  {PASS if ok else FAIL}  {fname}")
    if not ok:
        all_ok = False

# -------------------------------------------------------------------
# TEST 2: Files ton tai tren disk
# -------------------------------------------------------------------
sep("TEST 2: CSV files ton tai tren disk")
vi_dir = os.path.join(os.path.dirname(__file__), 'data_ingestion', 'vietnamese_data')
for fname in vi_files:
    fpath = os.path.join(vi_dir, fname)
    exists = os.path.isfile(fpath)
    size_mb = os.path.getsize(fpath) / 1024 / 1024 if exists else 0
    status = PASS if exists else FAIL
    print(f"  {status}  {fname}  ({size_mb:.1f} MB)")

# -------------------------------------------------------------------
# TEST 3: Encoding & cot du lieu dung
# -------------------------------------------------------------------
sep("TEST 3: Encoding UTF-8-sig & column names")
for fname in vi_files:
    fpath = os.path.join(vi_dir, fname)
    if not os.path.isfile(fpath):
        continue
    try:
        with open(fpath, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            cols = reader.fieldnames
            row = next(reader)
            has_text  = 'text' in cols
            has_label = 'label' in cols
            has_viet  = any(ord(c) > 127 for c in row.get('text',''))
            print(f"  {PASS if (has_text and has_label) else FAIL}  {fname}")
            print(f"         columns={cols}")
            print(f"         unicode_chars={'YES' if has_viet else 'NO'}")
            print(f"         sample_text='{row.get('text','')[:60]}'")
            print(f"         sample_label='{row.get('label','')}'")
    except Exception as e:
        print(f"  {FAIL}  {fname}: {e}")

# -------------------------------------------------------------------
# TEST 4: Schema output cua generator
# -------------------------------------------------------------------
sep("TEST 4: Schema output {timestamp, textComment, topic, label}")
required_keys = {'timestamp', 'textComment', 'topic', 'label'}
errors = []
topics_seen = {}
records_checked = 0

for payload in stream_multisource_data():
    # Keys
    if set(payload.keys()) != required_keys:
        errors.append(f"Keys sai: {set(payload.keys())}")
        break
    # Types
    if not isinstance(payload['timestamp'], int):
        errors.append(f"timestamp phai int, got {type(payload['timestamp'])}")
    if not isinstance(payload['textComment'], str) or not payload['textComment'].strip():
        errors.append(f"textComment rong/sai type")
    if not isinstance(payload['topic'], str):
        errors.append(f"topic phai str")
    if payload['label'] not in (0, 1):
        errors.append(f"label phai 0 hoac 1, got {payload['label']}")
    # No raw newlines
    if any(c in payload['textComment'] for c in ['\r', '\n', '\t']):
        errors.append(f"textComment con newline/tab")

    t = payload['topic']
    topics_seen[t] = topics_seen.get(t, 0) + 1
    records_checked += 1
    if records_checked >= 3000:
        break

if errors:
    for e in errors[:5]:
        print(f"  {FAIL}  {e}")
else:
    print(f"  {PASS}  Schema chinh xac tren {records_checked} records")
    print(f"  {PASS}  Label values: {{0, 1}} only")
    for topic, cnt in sorted(topics_seen.items()):
        print(f"  {PASS}  topic '{topic}': {cnt} records sampled")

# -------------------------------------------------------------------
# TEST 5: Tat ca 4 streams deu duoc chon (random multiplex)
# -------------------------------------------------------------------
sep("TEST 5: Multiplexing - tat ca 4 streams hoat dong")
expected_topics = {
    'uit_vsfc', 'minhtoan_sentiment',
    'polarbear_sentiment', 'vietnamese_sentiment_combined'
}
got_topics = set(topics_seen.keys())
missing = expected_topics - got_topics
if missing:
    print(f"  {WARN}  Topics chua xuat hien (co the do random): {missing}")
else:
    print(f"  {PASS}  Tat ca 4 streams duoc multiplexed ngau nhien")

# -------------------------------------------------------------------
# TONG KET
# -------------------------------------------------------------------
sep("TONG KET")
total_fails = len(errors) + (1 if not all_ok else 0)
if total_fails == 0:
    print("  [ALL PASS] Moi thu hoat dong chinh xac!")
    print("  San sang push len remote va tich hop vao pipeline.")
else:
    print(f"  [{total_fails} FAIL] Can kiem tra lai cac loi tren.")
print()
