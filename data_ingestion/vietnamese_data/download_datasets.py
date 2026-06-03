"""
Vietnamese Sentiment Dataset Downloader
========================================
Script tự động tải các dataset tieng Viet de huan luyen mo hinh sentiment.

Chay:
    pip install datasets pandas requests tqdm
    python download_datasets.py
"""

import os
import sys
import csv
import json
import time
import pandas as pd
from pathlib import Path

# Fix UTF-8 output tren Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OUTPUT_DIR = Path(__file__).parent
COMBINED_OUTPUT = OUTPUT_DIR / "vietnamese_sentiment_combined.csv"

# =========================================================
def save_csv(rows, filename):
    if not rows:
        print(f"  [!] Khong co du lieu: {filename}")
        return None
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / filename, index=False, encoding="utf-8-sig")
    print(f"  [OK] Da luu {len(df):,} dong --> {filename}")
    return df

# =========================================================
# DATASET 1 - UIT-VSFC (Vietnamese Students' Feedback Corpus)
# Source: https://huggingface.co/datasets/ura-hcmut/UIT-VSFC
# 16,175 cau phan hoi sinh vien: positive / negative / neutral
# Domain: Giao duc
# =========================================================
def download_uit_vsfc():
    print("\n[1/6] UIT-VSFC - Vietnamese Students Feedback Corpus")
    print("       HuggingFace: ura-hcmut/UIT-VSFC")
    try:
        from datasets import load_dataset
        ds = load_dataset("ura-hcmut/UIT-VSFC")
        label_map = {0: "negative", 1: "neutral", 2: "positive"}
        rows = []
        for split in ds:
            for item in ds[split]:
                text = item.get("text", "")
                label_raw = item.get("label", None)
                if label_raw is None:
                    continue  # skip rows without label
                if isinstance(label_raw, str):
                    label = label_raw.lower()
                else:
                    try:
                        label = label_map.get(int(label_raw), "neutral")
                    except (TypeError, ValueError):
                        continue
                if text and text.strip():
                    rows.append({
                        "text": text, "label": label,
                        "source": "UIT-VSFC", "domain": "education", "split": split
                    })
        return save_csv(rows, "uit_vsfc.csv")
    except Exception as e:
        print(f"  [ERR] {e}")
        return None


# =========================================================
# DATASET 2 - Vietnamese Comment Sentiment (minhtoan)
# Source: https://huggingface.co/datasets/minhtoan/vietnamese-comment-sentiment
# Comment mang xa hoi tieng Viet, 3 nhan pos/neg/neu
# =========================================================
def download_minhtoan_sentiment():
    print("\n[2/6] Vietnamese News/Social Media Sentiment (minhtoan) - ~13,132 dong")
    print("       HuggingFace: minhtoan/vietnamese-comment-sentiment")
    print("       Domain: Bao chi tai chinh, Facebook (nhan: Tich cuc/Tieu cuc/Trung lap)")
    try:
        from datasets import load_dataset
        ds = load_dataset("minhtoan/vietnamese-comment-sentiment")
        # Columns: 'Content' (text), 'Sentiment' (Tich cuc / Tieu cuc / Trung lap)
        viet_label_map = {
            "tich cuc": "positive",
            "tích cực": "positive",
            "positive": "positive",
            "tieu cuc": "negative",
            "tiêu cực": "negative",
            "negative": "negative",
            "trung lap": "neutral",
            "trung lập": "neutral",
            "neutral": "neutral",
        }
        rows = []
        for split in ds:
            for item in ds[split]:
                # Dung 'Content' (full article) hoac 'BriefContent' (ngan hon)
                text = item.get("BriefContent") or item.get("Content", "")
                sentiment_raw = str(item.get("Sentiment", "")).strip().lower()
                label = viet_label_map.get(sentiment_raw, None)
                if label is None:
                    continue  # bo qua dong khong co nhan hop le
                if text and text.strip():
                    rows.append({
                        "text": text.strip(), "label": label,
                        "source": "minhtoan-vi-news", "domain": "news_finance", "split": split
                    })
        return save_csv(rows, "minhtoan_sentiment.csv")
    except Exception as e:
        print(f"  [ERR] {e}")
        return None


# =========================================================
# DATASET 3 - Vietnamese Reviews (e-commerce tong hop)
# Source: https://huggingface.co/datasets/Vietnamese/vietnamese-sentiment-analysis
# Tong hop reviews tu nhieu nguon thuong mai dien tu
# =========================================================
def download_viet_ecommerce():
    print("\n[3/6] Vietnamese E-commerce Reviews (tong hop)")
    # Thu nhieu ID kha nang ton tai
    candidates = [
        "lpmxl/Vietnamese-Sentiment-Analysis",
        "Libosa/Vietnamese-Sentiment-Analysis",
        "silversearch/vietnamese_reviews",
        "vietnamese/sentiment",
    ]
    for hf_id in candidates:
        try:
            from datasets import load_dataset
            print(f"       Thu: {hf_id}")
            ds = load_dataset(hf_id)
            rows = []
            for split in ds:
                for item in ds[split]:
                    text = item.get("text", item.get("review", item.get("comment", "")))
                    label_raw = str(item.get("label", item.get("sentiment", ""))).lower()
                    if "pos" in label_raw or label_raw in ["1", "2"]: label = "positive"
                    elif "neg" in label_raw or label_raw == "0": label = "negative"
                    else: label = "neutral"
                    if text and text.strip():
                        rows.append({"text": text, "label": label,
                                     "source": hf_id.split("/")[-1], "domain": "ecommerce", "split": split})
            if rows:
                return save_csv(rows, "viet_ecommerce.csv")
        except Exception as e:
            print(f"  [ERR] {hf_id}: {e}")
    print("  [!] Khong tim thay dataset e-commerce nao hoat dong tren HuggingFace.")
    print("      --> Tai thu cong tu Kaggle (xem phan MANUAL bên duoi)")
    return None


# =========================================================
# DATASET 4 - Vietnamese SA (anotherpolarbear)
# Source: https://huggingface.co/datasets/anotherpolarbear/vietnamese-sentiment-analysis
# ~10,000 dong tu e-commerce + mang xa hoi
# =========================================================
def download_polarbear():
    print("\n[4/6] Vietnamese Sentiment (anotherpolarbear) - 10,010 dong")
    print("       HuggingFace: anotherpolarbear/vietnamese-sentiment-analysis")
    try:
        from datasets import load_dataset
        ds = load_dataset("anotherpolarbear/vietnamese-sentiment-analysis")
        rows = []
        for split in ds:
            for item in ds[split]:
                text = item.get("text", item.get("comment", item.get("sentence", "")))
                label_raw = item.get("label", item.get("sentiment", ""))
                if isinstance(label_raw, int):
                    lmap = {0: "negative", 1: "neutral", 2: "positive"}
                    label = lmap.get(label_raw, "neutral")
                else:
                    ls = str(label_raw).lower()
                    if "pos" in ls or ls in ["1", "2"]: label = "positive"
                    elif "neg" in ls or ls == "0": label = "negative"
                    else: label = "neutral"
                if text:
                    rows.append({
                        "text": text, "label": label,
                        "source": "polarbear-vi-SA", "domain": "mixed", "split": split
                    })
        return save_csv(rows, "polarbear_sentiment.csv")
    except Exception as e:
        print(f"  [ERR] {e}")
        return None


# =========================================================
# DATASET 5 - ViOCD (Vietnamese Opinion Corpus)
# Source: https://huggingface.co/datasets/PhamHuyHiep45200/ViOCD
# Comment tren mang xa hoi Viet Nam
# =========================================================
def download_viocd():
    print("\n[5/6] Vietnamese NLP - Multiple sources")
    # Thu nhieu dataset backup
    candidates = [
        ("duyth04/vietnamese_sentiment_analysis", "text", "label"),
        ("SentimentVN/vietnamese-sentiment", "text", "label"),
        ("anti-hb/vietnamese-sentiment", "text", "label"),
    ]
    for hf_id, text_col, label_col in candidates:
        try:
            from datasets import load_dataset
            print(f"       Thu: {hf_id}")
            ds = load_dataset(hf_id)
            rows = []
            for split in ds:
                for item in ds[split]:
                    text = item.get(text_col, item.get("sentence", item.get("comment", "")))
                    label_raw = str(item.get(label_col, item.get("sentiment", ""))).lower()
                    if "pos" in label_raw or label_raw in ["1", "2"]: label = "positive"
                    elif "neg" in label_raw or label_raw in ["0", "-1"]: label = "negative"
                    else: label = "neutral"
                    if text and text.strip():
                        rows.append({"text": text, "label": label,
                                     "source": hf_id.split("/")[-1], "domain": "mixed", "split": split})
            if rows:
                return save_csv(rows, "viocd.csv")
        except Exception as e:
            print(f"  [ERR] {hf_id}: {type(e).__name__}")
    print("  [!] Khong co dataset backup nao kha dung.")
    return None


# =========================================================
# DATASET 6 - Vietnamese NLP Datasets (SEACrowd collection)
# Source: https://huggingface.co/datasets/SEACrowd/uit_vsfc
# Bo suu tap tieng Viet cua SEACrowd
# =========================================================
def download_seacrowd_vsfc():
    print("\n[6/6] HSD Vietnamese (vlsp-shared-tasks)")
    candidates = [
        "phongnt04/vlsp-2021-hsd",
        "vi-nlp/hate-speech",
        "MrNobody33/VN_sentiment_training",
    ]
    for hf_id in candidates:
        try:
            from datasets import load_dataset
            print(f"       Thu: {hf_id}")
            ds = load_dataset(hf_id)
            rows = []
            for split in ds:
                for item in ds[split]:
                    text = item.get("text", item.get("sentence", item.get("free_text", "")))
                    label_raw = str(item.get("label", item.get("sentiment", ""))).lower()
                    if "pos" in label_raw or label_raw in ["1", "clean"]: label = "positive"
                    elif "neg" in label_raw or label_raw in ["0", "-1", "hate", "offensive"]: label = "negative"
                    else: label = "neutral"
                    if text and text.strip():
                        rows.append({"text": text, "label": label,
                                     "source": hf_id.split("/")[-1], "domain": "social_media", "split": split})
            if rows:
                return save_csv(rows, "seacrowd_vsfc.csv")
        except Exception as e:
            print(f"  [ERR] {hf_id}: {type(e).__name__}")
    print("  [!] Khong co dataset HSD nao kha dung.")
    return None


# =========================================================
# BONUS: Manual dataset guides
# =========================================================
def print_manual_guides():
    print("\n" + "="*60)
    print("[MANUAL] Cac dataset can tai thu cong:")
    print("="*60)
    print("""
[A] VLSP 2016 Sentiment (Hotel & Restaurant reviews)
    Dang ky: https://vlsp.org.vn/resources
    --> Dat file vao thu muc nay: vlsp2016_hotel.csv, vlsp2016_restaurant.csv

[B] Shopee Vietnamese Reviews (Kaggle)
    pip install kaggle
    kaggle datasets download -d nhanvo/shopee-vietnamese-product-reviews-sentiment
    URL: https://www.kaggle.com/datasets/nhanvo/shopee-vietnamese-product-reviews-sentiment

[C] Synthetic Vietnamese Feedback (Kaggle)
    kaggle datasets download -d ltkien03/synthetic-vietnamese-students-feedback-corpus
    URL: https://www.kaggle.com/datasets/ltkien03/synthetic-vietnamese-students-feedback-corpus

[D] ViNLP Vietnamese Sentiment (GitHub)
    git clone https://github.com/vinai-research/vinlp
    --> Xem thu muc data/

    Format mong doi sau khi dat file:
    text,label (label: positive/negative/neutral)
""")


# =========================================================
# COMBINE
# =========================================================
def combine_all():
    print("\n" + "="*60)
    print("TONG HOP TAT CA DATASETS")
    print("="*60)
    csvs = [
        "uit_vsfc.csv", "minhtoan_sentiment.csv", "viet_ecommerce.csv",
        "polarbear_sentiment.csv", "viocd.csv", "seacrowd_vsfc.csv",
        "vlsp2016_hotel.csv", "vlsp2016_restaurant.csv",
    ]
    dfs = []
    for f in csvs:
        p = OUTPUT_DIR / f
        if p.exists():
            df = pd.read_csv(p, encoding="utf-8-sig")
            if "text" in df.columns and "label" in df.columns:
                dfs.append(df[["text", "label", "source", "domain"]])
                print(f"  + {f}: {len(df):,} dong")
    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        combined = combined.dropna(subset=["text", "label"])
        combined = combined[combined["text"].str.strip() != ""]
        combined.to_csv(COMBINED_OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n  --> File tong hop: {COMBINED_OUTPUT.name}")
        print(f"  Tong: {len(combined):,} dong")
        print("\n  Phan phoi nhan:")
        print(combined["label"].value_counts().to_string())
        print("\n  Nguon:")
        print(combined["source"].value_counts().to_string())
    else:
        print("  [!] Chua co file CSV nao!")


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    print("="*60)
    print("Vietnamese Sentiment Dataset Downloader v2.0")
    print("="*60)
    print(f"Output: {OUTPUT_DIR}")

    try:
        from datasets import load_dataset
        import pandas as pd
    except ImportError:
        print("\n[ERR] Thieu thu vien! Chay:")
        print("      pip install datasets pandas tqdm")
        sys.exit(1)

    download_uit_vsfc()
    download_minhtoan_sentiment()
    download_viet_ecommerce()
    download_polarbear()
    download_viocd()
    download_seacrowd_vsfc()
    print_manual_guides()
    combine_all()

    print("\n" + "="*60)
    print("[DONE] Kiem tra thu muc:", OUTPUT_DIR)
    print("="*60)
