import argparse
from pathlib import Path
import pandas as pd

def main():
    p = argparse.ArgumentParser(description="Validate and normalize labelled clause CSV.")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--text-column", default="text")
    p.add_argument("--label-column", default="label")
    a = p.parse_args()
    df = pd.read_csv(a.input)
    if a.text_column not in df or a.label_column not in df:
        raise SystemExit("CSV must contain the configured text and label columns.")
    df = df[[a.text_column, a.label_column]].dropna()
    df.columns = ["text", "label"]
    df["text"] = df.text.astype(str).str.strip()
    df["label"] = df.label.astype(str).str.strip()
    df = df[(df.text != "") & (df.label != "")].drop_duplicates()
    if df.label.nunique() < 2:
        raise SystemExit("At least two labels are required.")
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.output, index=False)
    print(f"Saved {len(df)} examples across {df.label.nunique()} labels to {a.output}")

if __name__ == "__main__":
    main()
