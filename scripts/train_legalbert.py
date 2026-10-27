
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from datasets import Dataset
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
from transformers import (
    AutoConfig,
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)


def load_split(path):
    """Load a prepared CUAD CSV and validate its columns."""
    if not path.exists():
        raise FileNotFoundError(
            f"Cannot find: {path}\n"
            "Run scripts/prepare_cuad.py first."
        )

    df = pd.read_csv(path)

    required = {"text", "label", "contract_id"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"{path} is missing columns: {sorted(missing)}"
        )

    df = df.dropna(
        subset=["text", "label", "contract_id"]
    ).copy()

    df["text"] = df["text"].astype(str).str.strip()
    df["label"] = df["label"].astype(str).str.strip().str.lower()
    df["contract_id"] = df["contract_id"].astype(str).str.strip()

    df = df[
        (df["text"] != "")
        & (df["label"] != "")
        & (df["contract_id"] != "")
    ]

    return df.reset_index(drop=True)


def check_splits(train, validation, test):
    """Check contract separation and label consistency."""
    train_ids = set(train["contract_id"])
    val_ids = set(validation["contract_id"])
    test_ids = set(test["contract_id"])

    if train_ids & val_ids:
        raise ValueError(
            "Contract leakage: training and validation share contracts."
        )

    if train_ids & test_ids:
        raise ValueError(
            "Contract leakage: training and test share contracts."
        )

    if val_ids & test_ids:
        raise ValueError(
            "Contract leakage: validation and test share contracts."
        )

    train_labels = set(train["label"])
    val_labels = set(validation["label"])
    test_labels = set(test["label"])

    if val_labels - train_labels:
        raise ValueError(
            "Labels occur in validation but not training: "
            + ", ".join(sorted(val_labels - train_labels))
        )

    if test_labels - train_labels:
        raise ValueError(
            "Labels occur in test but not training: "
            + ", ".join(sorted(test_labels - train_labels))
        )


def main():
    parser = argparse.ArgumentParser(
        description="Fine-tune LegalBERT on CUAD clause categories."
    )

    parser.add_argument(
        "--data-dir",
        default="data/processed",
    )
    parser.add_argument(
        "--model-name",
        default="nlpaueb/legal-bert-base-uncased",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/legalbert-clause-classifier",
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-length", type=int, default=256)

    a = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit(
            "CUDA is not available. Activate the correct .venv first."
        )

    if a.epochs < 1 or a.batch_size < 1 or a.max_length < 32:
        raise SystemExit(
            "Use epochs >= 1, batch-size >= 1, and max-length >= 32."
        )

    print("=" * 60)
    print("CONTRACT RISK ANALYZER: LEGALBERT TRAINING")
    print("=" * 60)
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(
        "GPU VRAM: "
        f"{torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB"
    )

    data_dir = Path(a.data_dir)

    train = load_split(data_dir / "cuad_train.csv")
    validation = load_split(data_dir / "cuad_validation.csv")
    test = load_split(data_dir / "cuad_test.csv")

    check_splits(train, validation, test)

    # The class mapping is built from the training set only.
    labels = sorted(train["label"].unique())
    label2id = {label: index for index, label in enumerate(labels)}
    id2label = {index: label for label, index in label2id.items()}

    print("\nDATASET SUMMARY")
    print("-" * 60)

    for name, frame in [
        ("Training", train),
        ("Validation", validation),
        ("Test", test),
    ]:
        print(
            f"{name}: {len(frame):,} rows | "
            f"{frame['label'].nunique()} labels | "
            f"{frame['contract_id'].nunique()} contracts"
        )

    print(f"\nTraining classes: {len(labels)}")

    print("\nLoading LegalBERT tokenizer and configuration...")
    tokenizer = AutoTokenizer.from_pretrained(a.model_name)

    config = AutoConfig.from_pretrained(a.model_name)
    config.num_labels = len(labels)
    config.label2id = label2id
    config.id2label = id2label

    # The pretrained language model weights are retained.
    # A new classification head is initialized for our CUAD labels.
    model = AutoModelForSequenceClassification.from_pretrained(
        a.model_name,
        config=config,
        ignore_mismatched_sizes=True,
    )

    def tokenize_split(frame):
        dataset = Dataset.from_dict({
            "text": frame["text"].tolist(),
            "labels": [
                label2id[label] for label in frame["label"]
            ],
        })

        return dataset.map(
            lambda batch: tokenizer(
                batch["text"],
                truncation=True,
                max_length=a.max_length,
            ),
            batched=True,
            desc="Tokenizing",
        )

    print("\nPreparing datasets...")
    train_ds = tokenize_split(train)
    val_ds = tokenize_split(validation)
    test_ds = tokenize_split(test)

    def compute_metrics(prediction):
        logits = prediction.predictions

        if isinstance(logits, tuple):
            logits = logits[0]

        guesses = np.argmax(logits, axis=-1)
        actual = prediction.label_ids

        return {
            "accuracy": accuracy_score(actual, guesses),
            "macro_f1": f1_score(
                actual,
                guesses,
                average="macro",
                zero_division=0,
            ),
            "weighted_f1": f1_score(
                actual,
                guesses,
                average="weighted",
                zero_division=0,
            ),
        }

    output_dir = Path(a.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # warmup_steps accepts a float ratio in compatible Transformers
    # versions; 0.06 means 6% of total training steps.
    training_args = TrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        learning_rate=2e-5,
        num_train_epochs=a.epochs,
        per_device_train_batch_size=a.batch_size,
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=4,
        weight_decay=0.01,
        warmup_steps=0.06,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        fp16=True,
        gradient_checkpointing=True,
        logging_strategy="steps",
        logging_steps=50,
        logging_first_step=True,
        report_to="none",
        seed=42,
        data_seed=42,
        dataloader_num_workers=0,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        processing_class=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )

    print("\nStarting training...")
    print("Batch size:", a.batch_size)
    print("Gradient accumulation:", 4)
    print("Effective batch size:", a.batch_size * 4)
    print("Maximum token length:", a.max_length)
    print("Mixed precision: enabled")
    print("\nKeep your laptop plugged in and this terminal open.\n")

    trainer.train()

    print("\nEvaluating on the held-out test set...")
    result = trainer.predict(test_ds)

    logits = result.predictions
    if isinstance(logits, tuple):
        logits = logits[0]

    predictions = np.argmax(logits, axis=-1)
    actual = result.label_ids

    report = classification_report(
        actual,
        predictions,
        labels=list(range(len(labels))),
        target_names=labels,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        actual,
        predictions,
        labels=list(range(len(labels))),
    )

    metrics = {
        "model_name": a.model_name,
        "accuracy": float(accuracy_score(actual, predictions)),
        "macro_f1": float(
            f1_score(
                actual,
                predictions,
                average="macro",
                zero_division=0,
            )
        ),
        "weighted_f1": float(
            f1_score(
                actual,
                predictions,
                average="weighted",
                zero_division=0,
            )
        ),
        "n_train": len(train),
        "n_validation": len(validation),
        "n_test": len(test),
        "labels": labels,
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
        "warning": (
            "This is a CUAD clause-category classifier, not a legal-risk "
            "severity model. Automatically generated 'other' examples "
            "may include relevant but unannotated clauses. Evaluate "
            "the model carefully before real-world use."
        ),
    }

    print("\nSaving model and evaluation results...")
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    (output_dir / "label_map.json").write_text(
        json.dumps(label2id, indent=2),
        encoding="utf-8",
    )

    (output_dir / "test_metrics.json").write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    pd.DataFrame(report).transpose().to_csv(
        output_dir / "classification_report.csv"
    )

    pd.DataFrame(
        matrix,
        index=labels,
        columns=labels,
    ).to_csv(output_dir / "confusion_matrix.csv")

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Accuracy:    {metrics['accuracy']:.4f}")
    print(f"Macro F1:    {metrics['macro_f1']:.4f}")
    print(f"Weighted F1: {metrics['weighted_f1']:.4f}")
    print(f"\nModel folder: {output_dir.resolve()}")
    print("Evaluation files saved successfully.")


if __name__ == "__main__":
    main()
