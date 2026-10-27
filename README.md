# Contract Risk Analyzer Pro

Frontend-agnostic contract screening starter: text/PDF/DOCX ingestion, explainable baseline rules, clause checks, FastAPI endpoints, and a LegalBERT fine-tuning pipeline.

**Important:** the initial risk engine is a heuristic baseline, not a trained or validated legal-risk model. LegalBERT inference is optional and requires a fine-tuned checkpoint. This tool is not legal advice.

## Install and run
Python 3.10 or 3.11 recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn contract_risk.api:app --reload
```

API docs: http://127.0.0.1:8000/docs

## Example
```bash
curl -X POST http://127.0.0.1:8000/v1/analyze -H "Content-Type: application/json" -d "{\"text\":\"The supplier may terminate this agreement at any time without notice.\"}"
```

## Train
Prepare `data/raw/clauses.csv` with columns `text,label`, then:

```bash
pip install -e ".[training]"
python scripts/prepare_csv.py --input data/raw/clauses.csv --output data/processed/clauses.csv
python scripts/train_legalbert.py --data data/processed/clauses.csv --output-dir artifacts/legalbert-clause-classifier
```

Configure inference with `CONTRACT_RISK_MODEL=artifacts/legalbert-clause-classifier` before starting the API. The trained model predicts clause categories, not legal risk severity.

CUAD dataset: https://www.atticusprojectai.org/cuad/ . Review its terms and the upstream LegalBERT model card/license before redistribution. CUAD does not provide general low/medium/high risk labels. Do not invent them.

## Before public deployment
Add authentication, TLS, rate limits, upload limits, retention/deletion policies, and privacy-safe logging. Review false positives with qualified legal professionals. The risk score is a transparent heuristic, not a probability of loss. OCR for scanned PDFs is not included yet.
