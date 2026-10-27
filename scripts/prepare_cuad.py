
import json
import random
import re
from pathlib import Path

import pandas as pd

SEED = 42
MIN_TEXT_CHARS = 15
MAX_TEXT_CHARS = 1500

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "processed"
CATEGORY_FILE = RAW / "category_descriptions.csv"


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"]

    if isinstance(payload, list):
        return payload

    raise ValueError(f"Unexpected JSON format: {path}")



def normalize_label(question):
    """Extract only the CUAD category name from its question."""
    question = str(question or "")

    # CUAD question format:
    # Highlight ... related to "Document Name"
    # that should be reviewed by a lawyer. Details: ...

    match = re.search(
        r"related to\s*[\"“]?(.+?)[\"”]?\s+"
        r"that should be reviewed by a lawyer",
        question,
        flags=re.IGNORECASE,
    )

    if match:
        label = match.group(1)
    else:
        # Fallback for questions with slightly different formatting.
        match = re.search(
            r'related to\s*["“]([^"”]+)["”]',
            question,
            flags=re.IGNORECASE,
        )
        if match:
            label = match.group(1)
        else:
            return "unknown"

    label = re.sub(r"\s+", " ", label).strip(" .:-")
    label = label.lower().replace("/", " ").replace("-", " ")
    return re.sub(r"\s+", " ", label).strip()


def get_answers(qa):
    answers = qa.get("answers", [])

    if isinstance(answers, dict):
        answers = [answers]

    return answers if isinstance(answers, list) else []


def build_examples(documents, split_name):
    rows = []
    rng = random.Random(SEED)

    for doc_index, doc in enumerate(documents):
        title = str(doc.get("title") or f"{split_name}_{doc_index}")
        contract_id = f"{split_name}:{doc_index}:{title}"

        paragraphs = doc.get("paragraphs", [])
        if not isinstance(paragraphs, list):
            continue

        positive_spans = []
        negative_candidates = []

        for paragraph in paragraphs:
            if not isinstance(paragraph, dict):
                continue

            context = str(paragraph.get("context") or "")
            if not context:
                continue

            qas = paragraph.get("qas", [])
            if not isinstance(qas, list):
                continue

            paragraph_spans = []

            for qa in qas:
                if not isinstance(qa, dict):
                    continue

                label = normalize_label(qa.get("question", ""))

                for answer in get_answers(qa):
                    if not isinstance(answer, dict):
                        continue

                    raw_text = str(answer.get("text") or "")
                    text = re.sub(r"\s+", " ", raw_text).strip()

                    if not (MIN_TEXT_CHARS <= len(text) <= MAX_TEXT_CHARS):
                        continue

                    answer_start = answer.get("answer_start")

                    try:
                        answer_start = int(answer_start)
                    except (TypeError, ValueError):
                        answer_start = context.find(raw_text)

                    if answer_start < 0:
                        continue

                    answer_end = answer_start + len(raw_text)

                    if answer_end > len(context):
                        continue

                    # Verify the source span before trusting its offsets.
                    if context[answer_start:answer_end] != raw_text:
                        continue

                    paragraph_spans.append((answer_start, answer_end))

                    positive_spans.append({
                        "text": text,
                        "label": label,
                        "contract_id": contract_id,
                    })

            # Generate a limited number of candidate negatives.
            # These are approximate negatives, not verified legal negatives.
            sentence_pattern = re.compile(r"[^.!?\n]+(?:[.!?]+|$)|\n+")

            for match in sentence_pattern.finditer(context):
                start, end = match.span()
                text = match.group().strip()

                if not (MIN_TEXT_CHARS <= len(text) <= MAX_TEXT_CHARS):
                    continue

                if any(
                    start < answer_end and end > answer_start
                    for answer_start, answer_end in paragraph_spans
                ):
                    continue

                negative_candidates.append({
                    "text": text,
                    "label": "other",
                    "contract_id": contract_id,
                })

        rows.extend(positive_spans)

        rng.shuffle(negative_candidates)

        # Limit negatives relative to positives, so "other" does not
        # overwhelm every target category.
        negative_limit = min(
            30,
            max(3, len(positive_spans)),
        )

        rows.extend(negative_candidates[:negative_limit])

    df = pd.DataFrame(
        rows,
        columns=["text", "label", "contract_id"],
    )

    if df.empty:
        raise ValueError(f"No examples extracted from {split_name}.")

    df["text"] = df["text"].astype(str).str.strip()
    df["label"] = df["label"].astype(str).str.strip().str.lower()

    df = df[
        df["text"].str.len().between(MIN_TEXT_CHARS, MAX_TEXT_CHARS)
        & (df["label"] != "")
    ]

    return df.drop_duplicates(
        subset=["text", "label", "contract_id"]
    ).reset_index(drop=True)


def split_validation(train_df, fraction=0.111111):
    """Reserve approximately 10% of original training contracts."""
    contract_ids = sorted(train_df["contract_id"].unique())

    if len(contract_ids) < 10:
        raise ValueError("Not enough contracts to create validation data.")

    rng = random.Random(SEED)
    rng.shuffle(contract_ids)

    validation_count = max(1, round(len(contract_ids) * fraction))
    validation_ids = set(contract_ids[:validation_count])

    validation = train_df[
        train_df["contract_id"].isin(validation_ids)
    ].copy()

    train = train_df[
        ~train_df["contract_id"].isin(validation_ids)
    ].copy()

    return (
        train.reset_index(drop=True),
        validation.reset_index(drop=True),
    )


def main():
    print("Preparing CUAD using official contract splits...")

    if not CATEGORY_FILE.exists():
        raise FileNotFoundError(
            f"Missing category reference file: {CATEGORY_FILE}"
        )

    categories = pd.read_csv(CATEGORY_FILE)

    if len(categories) != 41:
        print(
            f"WARNING: Expected 41 category rows, found {len(categories)}."
        )

    official_train = load_json(RAW / "train_separate_questions.json")
    official_test = load_json(RAW / "test.json")

    print(f"Official training contracts: {len(official_train)}")
    print(f"Official test contracts: {len(official_test)}")

    train_all = build_examples(official_train, "official_train")
    test = build_examples(official_test, "official_test")

    train, validation = split_validation(train_all)

    train_ids = set(train["contract_id"])
    validation_ids = set(validation["contract_id"])
    test_ids = set(test["contract_id"])

    assert not train_ids & validation_ids
    assert not train_ids & test_ids
    assert not validation_ids & test_ids

    OUTPUT.mkdir(parents=True, exist_ok=True)

    outputs = {
        "cuad_train.csv": train,
        "cuad_validation.csv": validation,
        "cuad_test.csv": test,
    }

    for filename, frame in outputs.items():
        path = OUTPUT / filename
        frame.to_csv(path, index=False, encoding="utf-8")
        print(
            f"Saved {len(frame):,} examples -> {path}"
        )

    print("\nTRAINING LABEL COUNTS")
    print(train["label"].value_counts().head(20).to_string())

    print("\nSUMMARY")
    print(f"Train:      {len(train):,} rows")
    print(f"Validation: {len(validation):,} rows")
    print(f"Test:       {len(test):,} rows")
    print(f"Categories in training: {train['label'].nunique()}")
    print(f"Categories in test:     {test['label'].nunique()}")

    print(
        "\nIMPORTANT: 'other' samples are heuristic negatives. "
        "This dataset trains clause-category classification, "
        "not legal-risk severity."
    )


if __name__ == "__main__":
    main()
