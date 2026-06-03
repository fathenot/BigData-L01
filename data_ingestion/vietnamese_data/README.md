# 🇻🇳 Nguồn Dataset Tiếng Việt — Sentiment Analysis

Folder này chứa các dataset tiếng Việt dùng để huấn luyện / finetune mô hình sentiment analysis.

---

## 📂 Cấu trúc thư mục

```
vietnamese_data/
├── download_datasets.py          ← Script tự động tải (chạy cái này trước)
├── README.md                     ← File này
│
├── [Auto-generated sau khi chạy script]
├── uit_vsfc.csv                  ← UIT-VSFC: 16,175 câu phản hồi sinh viên
├── uit_vsmec.csv                 ← UIT-VSMEC: 6,927 câu mạng xã hội  
├── vihsd.csv                     ← ViHSD: 33,400 câu Facebook
├── polarbear_sentiment.csv       ← Vietnamese SA tổng hợp: ~10,000 dòng
│
├── [Cần tải thủ công]
├── vlsp2016_hotel.csv            ← VLSP 2016: Review khách sạn (cần đăng ký)
├── vlsp2016_restaurant.csv       ← VLSP 2016: Review nhà hàng (cần đăng ký)
│
└── vietnamese_sentiment_combined.csv ← File tổng hợp tất cả nguồn
```

---

## 🚀 Cách tải nhanh (Auto)

```bash
# Cài thư viện
pip install datasets pandas tqdm requests

# Chạy script
python download_datasets.py
```

Script sẽ tự động tải các dataset từ HuggingFace và lưu vào thư mục này.

---

## 📊 Danh sách Dataset Chi Tiết

### 1. ✅ UIT-VSFC (Tự động)
| Thuộc tính | Giá trị |
|------------|---------|
| **Tên đầy đủ** | Vietnamese Students' Feedback Corpus |
| **Số lượng** | 16,175 câu |
| **Nhãn** | positive / negative / neutral |
| **Domain** | Giáo dục (phản hồi SV về giảng viên, CTĐT, CSVC) |
| **HuggingFace** | `uitnlp/vietnamese_students_feedback` |
| **Paper** | [Nguyen et al., 2018](https://aclanthology.org/W18-6114/) |

```python
from datasets import load_dataset
ds = load_dataset("uitnlp/vietnamese_students_feedback")
```

---

### 2. ✅ UIT-VSMEC (Tự động)
| Thuộc tính | Giá trị |
|------------|---------|
| **Tên đầy đủ** | Vietnamese Social Media Emotion Corpus |
| **Số lượng** | 6,927 câu |
| **Nhãn** | enjoyment / disgust / sadness / anger / surprise / fear / other |
| **Domain** | Mạng xã hội (Facebook, báo điện tử) |
| **HuggingFace** | `uitnlp/vsmec` |

```python
from datasets import load_dataset
ds = load_dataset("uitnlp/vsmec")
```

---

### 3. ✅ ViHSD (Tự động)
| Thuộc tính | Giá trị |
|------------|---------|
| **Tên đầy đủ** | Vietnamese Hate Speech Detection Dataset |
| **Số lượng** | 33,400 câu |
| **Nhãn** | CLEAN / OFFENSIVE / HATE |
| **Domain** | Facebook comments |
| **HuggingFace** | `phongnt/vihsd` |
| **Paper** | [Luu et al., 2021](https://arxiv.org/abs/2103.14110) |

```python
from datasets import load_dataset
ds = load_dataset("phongnt/vihsd")
```

---

### 4. ✅ Vietnamese Sentiment (anotherpolarbear) (Tự động)
| Thuộc tính | Giá trị |
|------------|---------|
| **Số lượng** | ~10,000 dòng |
| **Nhãn** | positive / negative / neutral |
| **Domain** | Tổng hợp (thương mại điện tử + mạng xã hội) |
| **HuggingFace** | `anotherpolarbear/vietnamese-sentiment-analysis` |

---

### 5. ⚠️ VLSP 2016 SA (Cần đăng ký)
| Thuộc tính | Giá trị |
|------------|---------|
| **Tên đầy đủ** | VLSP 2016 Shared Task: Sentiment Analysis |
| **Domain** | Hotel reviews + Restaurant reviews |
| **Nhãn** | positive / negative / neutral |
| **Đăng ký** | https://vlsp.org.vn/resources |
| **Mirror** | https://github.com/undertheseanlp/sentiment |

**Cách đăng ký:**
1. Vào https://vlsp.org.vn/resources
2. Chọn "Sentiment Analysis" → điền form
3. Nhận email với link download
4. Đặt file vào thư mục này, đổi tên thành `vlsp2016_hotel.csv`

---

### 6. ⚠️ Shopee Vietnamese Reviews (Cần Kaggle account)
| Thuộc tính | Giá trị |
|------------|---------|
| **Số lượng** | ~10,000 review Shopee.vn |
| **Nhãn** | positive / negative |
| **Domain** | Thương mại điện tử (Shopee) |
| **Kaggle** | `nhanvo/shopee-vietnamese-product-reviews-sentiment` |

```bash
pip install kaggle
kaggle datasets download -d nhanvo/shopee-vietnamese-product-reviews-sentiment
```

---

### 7. ⚠️ Synthetic Vietnamese Students Feedback (Cần Kaggle)
| Thuộc tính | Giá trị |
|------------|---------|
| **Số lượng** | 10,000+ câu (ChatGPT-generated) |
| **Nhãn** | positive / negative / neutral |
| **Kaggle** | `ltkien03/synthetic-vietnamese-students-feedback-corpus` |

---

## 🔗 Các nguồn bổ sung (Tìm thêm)

| Nguồn | URL | Loại |
|-------|-----|-------|
| UIT NLP Lab | https://nlp.uit.edu.vn/datasets | Học thuật |
| PhoBERT Datasets | https://github.com/VinAIResearch/PhoBERT | Nhiều loại |
| Vietnamese NLP Hub | https://github.com/kietnv/VietnameseDatasets | Tổng hợp |
| HuggingFace VI | https://huggingface.co/datasets?language=vi | Đa dạng |
| SEACrowd | https://huggingface.co/SEACrowd | Đông Nam Á |

---

## 📋 Format chuẩn (để tích hợp vào pipeline)

Mọi file CSV trong thư mục này phải có ít nhất 2 cột:

```csv
text,label
"Giáo viên dạy rất nhiệt tình và dễ hiểu","positive"
"Chương trình học quá nặng và nhàm chán","negative"
"Lớp học bình thường, không có gì đặc biệt","neutral"
```

**Giá trị hợp lệ cho `label`:** `positive` | `negative` | `neutral`

---

## 🔧 Tích hợp vào `data.py`

Sau khi có các file CSV, cập nhật `FILE_CONFIGS` trong `data.py`:

```python
FILE_CONFIGS = {
    # ... existing configs ...

    # Vietnamese datasets
    'uit_vsfc.csv': {
        'format': 'csv_with_header',
        'text_col': 'text',
        'label_col': 'label',
        'label_map': {'negative': 0, 'neutral': 0, 'positive': 1}
    },
    'vihsd.csv': {
        'format': 'csv_with_header',
        'text_col': 'text',
        'label_col': 'label',
        'label_map': {'negative': 0, 'neutral': 0, 'positive': 1}
    },
    # Thêm tương tự cho các file khác...
}
```
