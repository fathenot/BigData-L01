import csv
import json
import time
import re
import os
import random

FILE_CONFIGS = {
    'sentiment140.csv': {
        'format': 'csv_no_header',
        'text_col': 5,
        'label_col': 0,
        'label_map': {'0': 0, '4': 1}
    },
    'Cell_Phones_and_Accessories_5.json': {
        'format': 'json_lines',
        'text_col': 'reviewText',
        'label_col': 'overall',
        'label_map': {1.0: 0, 2.0: 0, 4.0: 1, 5.0: 1}
    },
    'train.csv' : {
        'format' : "csv_no_header",
        'text_col': 2,
        'label_col': 0,
        'label_map': {'1': 0, '2': 1} 
    },
    'amazon_reviews.csv': {
        'format' : "csv_with_header",
        'text_col': 'reviewText',
        'label_col': 'overall',
        'label_map': {'1.0': 0, '2.0': 0, '3.0': 0, '4.0': 1, '5.0': 1, }
    },

    # =====================================================================
    # VIETNAMESE DATASETS — added for multilingual training
    # Source: data_ingestion/vietnamese_data/
    # Schema output: {"timestamp", "textComment", "topic", "label"}
    # Label mapping: positive->1, negative->0, neutral->0
    # =====================================================================
    'uit_vsfc.csv': {
        'format': 'csv_with_header',
        'text_col': 'text',
        'label_col': 'label',
        'label_map': {
            'positive': 1,
            'negative': 0,
            'neutral':  0,
        }
    },
    'minhtoan_sentiment.csv': {
        'format': 'csv_with_header',
        'text_col': 'text',
        'label_col': 'label',
        'label_map': {
            'positive': 1,
            'negative': 0,
            'neutral':  0,
        }
    },
    'polarbear_sentiment.csv': {
        'format': 'csv_with_header',
        'text_col': 'text',
        'label_col': 'label',
        'label_map': {
            'positive': 1,
            'negative': 0,
            'neutral':  0,
        }
    },
    'vietnamese_sentiment_combined.csv': {
        'format': 'csv_with_header',
        'text_col': 'text',
        'label_col': 'label',
        'label_map': {
            'positive': 1,
            'negative': 0,
            'neutral':  0,
        }
    },
}


def get_file_generator(file_path, config, topic_tag):
    
    if config['format'] == 'csv_no_header':
        with open(file_path, 'r', encoding='latin-1') as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    if len(row) <= max(config['text_col'], config['label_col']): continue
                    raw_text = str(row[config['text_col']])
                    raw_label = str(row[config['label_col']])
                    if raw_label not in config['label_map']: continue
                    
                    label = config['label_map'][raw_label]
                    clean_text = re.sub(r'[\r\n\t]', ' ', raw_text)
                    yield {"timestamp": int(time.time()), "textComment": clean_text, "topic": topic_tag, "label": label}
                except Exception: continue

    elif config['format'] == 'csv_with_header':
        with open(file_path, 'r', encoding='utf-8-sig') as f:   # utf-8-sig strips BOM
            
            reader = csv.DictReader(f) 
            
            for row in reader:
                try:
                    raw_text = row.get(config['text_col'], "")
                    raw_label = str(row.get(config['label_col'], ""))
                    
                    if not raw_text or raw_label not in config['label_map']: 
                        continue
                        
                    label = config['label_map'][raw_label]
                    clean_text = re.sub(r'[\r\n\t]', ' ', str(raw_text))
                    
                    yield {
                        "timestamp": int(time.time()), 
                        "textComment": clean_text, 
                        "topic": topic_tag, 
                        "label": label
                    }
                except Exception: 
                    continue


    elif config['format'] == 'json_lines':
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    raw_text = data.get(config['text_col'], "")
                    raw_label = data.get(config['label_col'])
                    if not raw_text or raw_label not in config['label_map']: continue
                    
                    label = config['label_map'][raw_label]
                    clean_text = re.sub(r'[\r\n\t]', ' ', str(raw_text))
                    yield {"timestamp": int(time.time()), "textComment": clean_text, "topic": topic_tag, "label": label}
                except json.JSONDecodeError: continue

def stream_multisource_data(folder_path='./raw_data'):
    """
    Multiplex multiple data streams randomly.
    Searches for matching files in:
      1. folder_path (default: ./raw_data)  — English datasets
      2. ./data_ingestion/vietnamese_data/  — Vietnamese datasets
    """

    SEARCH_FOLDERS = [
        folder_path,
        os.path.join(os.path.dirname(__file__), 'data_ingestion', 'vietnamese_data'),
    ]

    all_files = []
    for search_dir in SEARCH_FOLDERS:
        if not os.path.isdir(search_dir):
            continue
        for f in os.listdir(search_dir):
            if f in FILE_CONFIGS:
                all_files.append((f, os.path.join(search_dir, f)))

    if not all_files:
        print(f"[EXTRACTOR] No valid data files found in: {SEARCH_FOLDERS}")
        return

    active_streams = []
    for file_name, file_path in all_files:
        config = FILE_CONFIGS[file_name]
        topic_tag = os.path.splitext(file_name)[0]
        gen = get_file_generator(file_path, config, topic_tag)
        active_streams.append((file_name, gen))
        print(f"[EXTRACTOR] Connected data stream to: {file_path}")

    print(f"\n[EXTRACTOR] Started multiplexing {len(active_streams)} data streams randomly!\n")

    while active_streams:
        idx = random.randrange(len(active_streams))
        file_name, gen = active_streams[idx]
        try:
            yield next(gen)
        except StopIteration:
            print(f"\n[EXTRACTOR] Stream '{file_name}' has finished broadcasting!")
            active_streams.pop(idx)