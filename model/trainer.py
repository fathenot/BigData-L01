import numpy as np
from datasets import load_dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)
import evaluate

print("Import successfully")

# ======================
# 1. CONFIG
# ======================
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"
DATA_PATH = "/kaggle/input/datasets/fegortranquoc/vietnamese-data/vietnamese_sentiment_combined.csv"

# ======================
# 2. MODEL + TOKENIZER
# ======================
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=3,
    ignore_mismatched_sizes=True
)

# ======================
# 3. DATASET
# ======================
dataset = load_dataset(
    "csv",
    data_files=DATA_PATH,
    split="train"
)

dataset = dataset.train_test_split(test_size=0.15, seed=42, shuffle=True)

train_dataset = dataset["train"]
eval_dataset = dataset["test"]

# ======================
# 4. LABEL ENCODING
# ======================
labels = sorted(set(train_dataset["label"]))
label2id = {l: i for i, l in enumerate(labels)}
id2label = {i: l for l, i in label2id.items()}

def preprocess(examples):
    tokens = tokenizer(
        examples["text"],
        truncation=True,
        max_length=128  # NO padding="max_length" → reduce RAM
    )

    tokens["labels"] = [label2id[l] for l in examples["label"]]
    return tokens

train_dataset = train_dataset.map(preprocess, batched=True)
eval_dataset = eval_dataset.map(preprocess, batched=True)

# remove raw columns → reduce memory
train_dataset = train_dataset.remove_columns(["text", "label", "source", "domain"])
eval_dataset = eval_dataset.remove_columns(["text", "label", "source", "domain"])

# ======================
# 5. DATA COLLATOR (dynamic padding)
# ======================
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# ======================
# 6. METRIC
# ======================
metric = evaluate.load("f1")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return metric.compute(
        predictions=preds,
        references=labels,
        average="macro"
    )

# ======================
# 7. TRAINING ARGS (KAGGLE OPTIMIZED)
# ======================
args = TrainingArguments(
    output_dir="./cardiff_vi",

    # performance-safe
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    gradient_accumulation_steps=4,

    learning_rate=2e-5,
    num_train_epochs=3,

    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,

    warmup_steps=300,
    weight_decay=0.01,

    fp16=True,  # IMPORTANT for Kaggle GPU

    logging_steps=50,
    dataloader_pin_memory=True
)

# ======================
# 8. TRAINER
# ======================
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    data_collator=data_collator,
    compute_metrics=compute_metrics
)

# ======================
# 9. TRAIN
# ======================
trainer.train()

# ======================
# 10. SAVE
# ======================
trainer.save_model("./cardiff_vi_finetuned")
tokenizer.save_pretrained("./cardiff_vi_finetuned")


import numpy as np
from sklearn.metrics import confusion_matrix, classification_report

predictions = trainer.predict(eval_dataset)

y_pred = np.argmax(predictions.predictions, axis=1)
y_true = predictions.label_ids

cm = confusion_matrix(y_true, y_pred)

print(cm)

print(classification_report(
    y_true,
    y_pred,
    digits=4
))
