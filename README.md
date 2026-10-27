 Contract Risk Analyzer Pro

An AI-assisted contract screening project that extracts contract text, identifies potentially important clauses, applies explainable rule-based checks, and returns a structured analysis report through a FastAPI backend.

The project is designed as a starting point for a contract analysis application that can later be extended with a web interface, additional legal clause categories, validated risk assessments, and a hosted API.

> Disclaimer: This project is for educational and informational screening purposes only. It does not provide legal advice, determine whether a contract is legally safe, or replace review by a qualified legal professional.

 Table of Contents

- [Features](features)
- [How It Works](how-it-works)
- [Technology Stack](technology-stack)
- [Project Structure](project-structure)
- [Requirements](requirements)
- [Installation](installation)
- [Running the API](running-the-api)
- [API Usage](api-usage)
- [LegalBERT Clause Classification](legalbert-clause-classification)
- [Dataset Preparation and Training](dataset-preparation-and-training)
- [Streamlit Interface](streamlit-interface)
- [Deployment](deployment)
- [Troubleshooting](troubleshooting)
- [Security and Privacy](security-and-privacy)
- [Limitations](limitations)
- [Licensing and Attribution](licensing-and-attribution)
- [Contributing](contributing)

 Features

- Document ingestion: Extract text from supported PDF, DOCX, and TXT files.
- Rule-based screening: Apply transparent rules to flag potentially concerning contract language.
- Clause categorization: Optionally classify clauses using a fine-tuned LegalBERT model.
- Structured results: Return findings, evidence, explanations, and recommendations where supported by the configured analysis engine.
- REST API: Expose analysis endpoints through FastAPI.
- Interactive API documentation: Test requests using Swagger UI.
- Training pipeline: Prepare labelled clause data and fine-tune a transformer classifier.
- Extensible architecture: Keep the analysis engine separate from the frontend so different clients can integrate with the API.

Feature availability depends on the files, model checkpoint, and configuration installed in your environment.

 How It Works

The application has three main components:

1. *Document processing: Extracts text from an uploaded document or accepts text directly.
2. Analysis engine: Applies heuristic rules and, when configured, LegalBERT clause classification.
3. API layer: Returns the analysis in JSON format through FastAPI.

The rule engine and the classifier have different purposes:

- The rule engine flags patterns that may deserve review and generates the current heuristic risk score.
- LegalBERT predicts clause categories learned from its training data.
- A clause-category prediction is not a prediction of legal risk severity, financial loss, or the probability of a dispute.

 Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| API framework | FastAPI |
| API server | Uvicorn |
| Document processing | PyMuPDF, docx2txt |
| Data preparation | pandas, scikit-learn |
| Machine learning | PyTorch, Hugging Face Transformers |
| Dataset format | CSV and JSON |
| Optional web interface | Streamlit |

 Project Structure

The following is a representative layout. Your repository may contain additional files.

```text
contract-risk-analyzer-pro/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── contract_risk/
│   ├── __init__.py
│   ├── api.py
│   ├── engine.py
│   ├── rules.py
│   ├── clauses.py
│   ├── documents.py
│   ├── schemas.py
│   └── model.py
├── data/
│   ├── raw/
│   └── processed/
├── scripts/
│   ├── prepare_csv.py
│   ├── prepare_cuad.py
│   └── train_legalbert.py
└── artifacts/
    └── legalbert-clause-classifier/
```

Some files and folders are optional. In particular, the trained model directory is required only when you want to run your own fine-tuned classifier.

 Requirements

- Python 3.10 or 3.11 is recommended for the original development setup. Use a Python version supported by all installed dependencies.
- Git, if you want to clone the repository.
- Internet access for installing dependencies and downloading pretrained model files.
- Additional disk space and memory for transformer models.
- An NVIDIA GPU is optional for training and may accelerate inference. CPU execution is possible but can be slower.

 Installation

 1. Clone the repository

Replace `YOUR_USERNAME` with the GitHub account that owns the repository.

```bash
git clone https://github.com/YOUR_USERNAME/AI-Based-Contract-Risk-Analyzer.git
cd AI-Based-Contract-Risk-Analyzer
```

Alternatively, download the repository as a ZIP file from GitHub and extract it.

 2. Create a virtual environment

Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

 3. Install dependencies

If the repository contains a `requirements.txt` file:

```bash
python -m pip install -r requirements.txt
```

If the project instead includes a valid `pyproject.toml` with development dependencies, follow the installation instructions defined there.

Do not run `pip install -e ".[dev]"` unless the repository actually contains the required project configuration.

 4. Verify the installation

```bash
python --version
python -m pip --version
```

If you plan to use the transformer model, verify PyTorch separately:

```bash
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
```

A CUDA-enabled PyTorch installation is optional. Follow the official [PyTorch installation selector](https://pytorch.org/get-started/locally/) to choose a compatible build for your operating system and hardware.

 Running the API

From the repository root, activate the virtual environment and run:

```bash
uvicorn contract_risk.api:app --reload
```

The local API should be available at:

- API base URL: `http://127.0.0.1:8000`
- Interactive Swagger documentation: `http://127.0.0.1:8000/docs`
- ReDoc documentation: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/health`

Keep the terminal running while you use the API. Press `Ctrl+C` to stop the development server.

The reload option is intended for local development, not production deployment.

 API Usage

 Analyze contract text

Endpoint: `POST /v1/analyze`

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/v1/analyze" \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"The supplier may terminate this agreement at any time without notice.\"}"
```

On Windows PowerShell, you can also use:

```powershell
$body = @{
    text = "The supplier may terminate this agreement at any time without notice."
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/v1/analyze" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

 Analyze a document

Endpoint: `POST /v1/analyze/file`

Use the interactive documentation at `http://127.0.0.1:8000/docs` to upload a supported file and inspect the response.

Alternatively, with curl:

```bash
curl -X POST "http://127.0.0.1:8000/v1/analyze/file" \
  -F "file=@sample_contract.pdf"
```

Replace `sample_contract.pdf` with the path to your own test document.

 Response format

The response schema depends on the API implementation. Depending on the configured engine, it may include:

- Overall heuristic risk score and risk level
- Clause statistics
- Potential findings
- Evidence and explanations
- Recommendations
- LegalBERT clause classifications
- Missing-clause checks
- A legal disclaimer

Use `/docs` to inspect the exact request fields and response schema for the version you are running.

 LegalBERT Clause Classification

The project can use a fine-tuned Hugging Face sequence-classification model stored locally.

The pretrained checkpoint used as the starting point is:

[`nlpaueb/legal-bert-base-uncased`](https://huggingface.co/nlpaueb/legal-bert-base-uncased)

The base checkpoint is not itself the project's trained clause classifier. Fine-tuning is required before using it for the project's custom clause categories.

 Configure the trained model

After training, set the `CONTRACT_RISK_MODEL` environment variable to the model directory.

Windows PowerShell

```powershell
$env:CONTRACT_RISK_MODEL = "artifacts/legalbert-clause-classifier"
uvicorn contract_risk.api:app --reload
```

macOS or Linux

```bash
export CONTRACT_RISK_MODEL="artifacts/legalbert-clause-classifier"
uvicorn contract_risk.api:app --reload
```

Run these commands from the repository root. The directory must contain the saved model and tokenizer files expected by the inference code.

If the model is not configured, the application may run without LegalBERT inference, depending on the implementation.

 Dataset Preparation and Training

 Prepare a custom CSV dataset

The generic preparation script expects a CSV with at least these columns:

| Column | Description |
|---|---|
| `text` | Clause text or text segment |
| `label` | Target clause category |

Example:

```csv
text,label
"The agreement is governed by California law.",governing_law
"Either party may terminate with 30 days notice.",termination
"The provider's liability shall not exceed fees paid.",limitation_of_liability
```

These rows are examples of the expected format, not a sufficient training dataset. A useful classifier needs many correctly labelled examples across each target category.

Prepare the CSV:

```bash
python scripts/prepare_csv.py \
  --input data/raw/clauses.csv \
  --output data/processed/clauses.csv
```

Train the classifier:

```bash
python scripts/train_legalbert.py \
  --data data/processed/clauses.csv \
  --output-dir artifacts/legalbert-clause-classifier
```

Check the available script arguments with:

```bash
python scripts/prepare_csv.py --help
python scripts/train_legalbert.py --help
```

Training can take a significant amount of time and memory. GPU acceleration is optional if the installed PyTorch build supports your GPU.

 CUAD dataset

The [Contract Understanding Atticus Dataset (CUAD)](https://www.atticusprojectai.org/cuad/) contains expert-annotated contract clauses across legal categories.

If using the project's CUAD preparation script, place the expected source JSON in the path required by that script, typically:

```text
data/raw/CUADv1.json
```

Then run:

```bash
python scripts/prepare_cuad.py
```

This command applies only if `scripts/prepare_cuad.py` is present in your checked-out version of the repository. Check the script's help or source code for supported arguments.

The generated datasets may include files such as:

```text
data/processed/
├── cuad_train.csv
├── cuad_validation.csv
└── cuad_test.csv
```

Important dataset limitations:

- CUAD is primarily a clause-identification and clause-category dataset, not a general legal-risk severity dataset.
- Dataset preparation heuristics can introduce incorrect labels, particularly for negative examples.
- Evaluate on contracts that are separate from the training contracts to reduce data leakage.
- Review category mappings, class balance, and sample annotations before relying on evaluation results.
- Do not interpret classification confidence as the probability that a clause is legally risky.

Review the dataset's applicable terms before redistribution or commercial use.

 Streamlit Interface

If the repository contains the Streamlit frontend at `app.py`, install Streamlit and Requests if they are not already included in your dependencies:

```bash
python -m pip install streamlit requests
```

Start the FastAPI backend in one terminal:

```bash
uvicorn contract_risk.api:app --reload
```

Open a second terminal in the repository root and start Streamlit:

```bash
python -m streamlit run app.py
```

Open the local URL printed in the terminal, usually `http://localhost:8501`.

If the frontend sends requests to `http://127.0.0.1:8000`, the API must be running on the same computer during local development.

 Deployment

 Streamlit Community Cloud

The frontend can be deployed on [Streamlit Community Cloud](https://share.streamlit.io/) when the repository contains a compatible Streamlit entry-point file and the necessary dependency configuration.

General steps:

1. Push the project to GitHub.
2. Confirm that the Streamlit entry-point file exists in the repository.
3. Add a compatible `requirements.txt`.
4. Sign in to Community Cloud using GitHub.
5. Select the repository, branch, and entry-point file.
6. Deploy the app and inspect its logs if startup fails.

See the official [Streamlit deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

 Important: the API is separate

Deploying the Streamlit frontend does not automatically deploy the FastAPI backend.

If the frontend calls `http://127.0.0.1:8000`, that address will refer to the Streamlit app's own remote environment after deployment, not your personal computer.

For the existing two-part architecture:

1. Deploy the FastAPI backend to a suitable hosting service.
2. Configure the Streamlit frontend to use the backend's public HTTPS URL.
3. Configure secrets and environment variables using the hosting platform's secret-management features.
4. Ensure the backend can access the trained model files.
5. Test file uploads, error handling, memory usage, and model startup time.

Community Cloud has resource limits, so loading a large transformer model directly into the Streamlit process may be impractical. Keeping model inference in a separately hosted API can make resource usage easier to manage.

Never publish private API keys, passwords, real contracts, or confidential client information in the Git repository.

 Troubleshooting

 `ModuleNotFoundError`

Activate the intended virtual environment and install the project's declared dependencies:

```bash
python -m pip install -r requirements.txt
```

Check that the `python` and `pip` commands refer to the same environment.

 `uvicorn` is not recognized

Run Uvicorn through Python:

```bash
python -m uvicorn contract_risk.api:app --reload
```

 The API cannot be reached

- Confirm that the backend terminal is still running.
- Open `http://127.0.0.1:8000/health`.
- Check that the frontend's API URL matches the backend address.
- Inspect the backend terminal for exceptions.

 PDF upload fails

- Confirm that PyMuPDF is installed.
- Test extraction from the file independently.
- Check the API response and backend logs.
- Confirm the file type and upload-size limits.
- Scanned PDFs may require OCR, which is not included in the current baseline unless separately implemented.

 LegalBERT does not load

- Verify that `CONTRACT_RISK_MODEL` points to the correct model directory.
- Confirm that the saved model and tokenizer files exist.
- Check that the model was trained for sequence classification.
- Confirm that PyTorch and Transformers are installed in the active environment.
- Review the API logs for model-loading errors.

 Streamlit deploys but analysis fails

- Verify that the backend has a public HTTPS endpoint.
- Ensure the frontend does not use `127.0.0.1` for a separately hosted backend.
- Check that all dependencies are declared in the deployment environment.
- Inspect Streamlit and backend logs for the actual exception.

 Security and Privacy

Contracts can contain confidential commercial information, personal information, trade secrets, and legally privileged material.

Before exposing this application to public users:

- Use HTTPS for network communication.
- Add authentication and rate limiting to the API.
- Validate file types and enforce upload-size limits.
- Avoid logging full contract text or other sensitive data.
- Establish retention and deletion policies.
- Protect secrets using environment variables or the host's secret manager.
- Restrict access to uploaded documents and generated reports.
- Review the privacy practices of all hosting providers and model services.
- Test file handling and error responses before production use.

Do not upload confidential contracts to a public demo unless you have assessed and communicated the applicable data-handling risks.

 Limitations

This project is an experimental screening tool. Its output can contain false positives, false negatives, incomplete clause extraction, and incorrect category predictions.

The current heuristic risk score is not a calibrated probability of loss or litigation. LegalBERT clause classification does not independently establish whether a contract is fair, enforceable, or safe to sign.

The baseline does not replace jurisdiction-specific legal analysis. Scanned-PDF OCR, production-grade access controls, comprehensive clause coverage, expert-validated risk labels, and formal model evaluation may require additional implementation.

All findings should be reviewed by a qualified legal professional before being used to make consequential decisions.

 Licensing and Attribution

Before distributing this project, review the licensing terms of every component, dataset, and pretrained model you use.

- LegalBERT: The [upstream model card](https://huggingface.co/nlpaueb/legal-bert-base-uncased) lists the model under CC BY-SA 4.0. Review its terms and attribution requirements before redistribution or commercial use.
- CUAD: Review the [official CUAD project page](https://www.atticusprojectai.org/cuad/) and the dataset's applicable terms.
- Dependencies: Each Python package has its own licence and usage conditions.

Add a root-level `LICENSE` file specifying the licence for your own code only after reviewing compatibility with third-party assets and intended use. Do not imply that third-party datasets or model weights are relicensed by your project's code licence.

 Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make focused changes and add tests where appropriate.
4. Verify the API and document-processing behavior locally.
5. Submit a pull request describing the changes and known limitations.

Please do not include real confidential contracts, personal data, credentials, or other sensitive information in issues, tests, or pull requests.

 Acknowledgements

This project builds on open-source tools and research, including FastAPI, Streamlit, PyTorch, Hugging Face Transformers, LegalBERT, and CUAD.

If you use or extend this project, retain appropriate attribution and respect the licences and terms of the original components.
