# API contract

- `GET /health`
- `POST /v1/analyze` JSON: `{"text":"...", "contract_type":"general"}`
- `POST /v1/analyze/file` multipart upload with `file` and optional `contract_type`

The response includes `schema_version`, `overall_risk_score`, `risk_level`, summary, word/clause statistics, findings, missing-clause checks, and disclaimer. The score is a heuristic prioritization score, not a probability of loss or estimate of monetary exposure.
