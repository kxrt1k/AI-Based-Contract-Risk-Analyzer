
import re
from collections import Counter

from .clauses import split_clauses
from .rules import detect_findings, missing_clause_checks, WEIGHT
from .schemas import AnalyzeResponse, ContractStatistics
from .model import classify_clause


def _has_governing_law(text: str) -> bool:
    """Recognize common ways contracts express governing law."""
    patterns = [
        r"\bgoverned\s+by\b",
        r"\bgoverning\s+law\b",
        r"\bconstrued\s+in\s+accordance\s+with\b",
        r"\blaws?\s+of\s+(?:the\s+)?(?:state\s+of\s+)?[A-Z]",
        r"\bsubject\s+to\s+the\s+laws?\s+of\b",
    ]
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in patterns
    )


def _get_missing_checks(text: str) -> list[str]:
    """Remove missing-clause warnings when the text already mentions them."""
    checks = missing_clause_checks(text)
    lower = text.lower()

    indicators = {
        "termination": [
            r"\bterminat(?:e|es|ed|ing|ion)\b",
            r"\bexpiration\b",
        ],
        "liability": [
            r"\bliabilit(?:y|ies)\b",
            r"\bindemnif(?:y|ies|ication)\b",
        ],
        "confidentiality": [
            r"\bconfidential\b",
            r"\bnon-disclosure\b",
        ],
        "dispute": [
            r"\bdispute resolution\b",
            r"\barbitration\b",
            r"\bjurisdiction\b",
            r"\bgoverning law\b",
            r"\bgoverned by\b",
            r"\bconstrued in accordance with\b",
            r"\blaws? of\b",
        ],
        "payment": [
            r"\bpayment\b",
            r"\bpay(?:s|able|ment)?\b",
            r"\binvoices?\b",
            r"\bfees?\b",
        ],
    }

    filtered = []

    for message in checks:
        message_lower = message.lower()
        matched_category = None

        for category in indicators:
            if category in message_lower:
                matched_category = category
                break

        if matched_category is None:
            filtered.append(message)
            continue

        # Governing law is recognized separately because phrases such
        # as "governed by California law" may omit "governing law".
        if matched_category == "dispute":
            if _has_governing_law(text):
                continue

            if any(
                re.search(pattern, lower, re.IGNORECASE)
                for pattern in indicators["dispute"][:3]
            ):
                continue

        elif any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in indicators[matched_category]
        ):
            continue

        filtered.append(message)

    return filtered


def analyze_text(
    text: str,
    contract_type: str = "general",
) -> AnalyzeResponse:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Contract text must be non-empty.")

    # 1. Split the document into clauses.
    clauses = split_clauses(text)

    # 2. Detect potential issues with the rule-based engine.
    findings = detect_findings(clauses)

    # 3. Classify clauses with LegalBERT.
    # Classification confidence describes model confidence, not legal risk.
    classifications = []

    for clause in clauses:
        if not clause.strip():
            continue

        try:
            prediction = classify_clause(clause)
        except Exception:
            # Keep the rule-based analyzer available if model inference fails.
            prediction = None

        if not prediction:
            continue

        label = str(prediction.get("label", "other"))
        confidence = float(prediction.get("score", 0.0))

        classifications.append(
            {
                "label": label,
                "confidence": max(0.0, min(1.0, confidence)),
                "text": clause,
            }
    )

    # 4. Calculate risk from rule findings only.
    # LegalBERT category labels are not legal-risk severity labels.
    weights = [WEIGHT[f.risk_level] for f in findings]

    if weights:
        score = min(
            100,
            round(
                12 * max(weights)
                + 4 * sum(weights)
                + min(12, len(findings) * 2)
            ),
        )
    else:
        score = 10 if len(text.split()) > 80 else 0

    if score >= 85:
        level = "critical"
    elif score >= 60:
        level = "high"
    elif score >= 30:
        level = "medium"
    else:
        level = "low"

    # 5. Summarize predicted categories.
    if classifications:
        label_counts = Counter(
            item["label"] for item in classifications
        )
        top_labels = label_counts.most_common(5)

        model_summary = ", ".join(
            f"{label} ({count})"
            for label, count in top_labels
        )

        summary = (
            f"Screening identified {len(findings)} potential issue(s) "
            f"using baseline rules. LegalBERT classified "
            f"{len(classifications)} clause(s). Common predicted "
            f"categories: {model_summary}. Review all findings in context."
        )
    else:
        summary = (
            f"Baseline screening identified {len(findings)} potential "
            "issue(s). LegalBERT classifications were unavailable, "
            "so the result relies on the existing rules."
        )

    # 6. Return findings, model predictions, statistics, and checks.
    # The classification field must exist in AnalyzeResponse.
    return AnalyzeResponse(
        contract_type=contract_type,
        overall_risk_score=score,
        risk_level=level,
        summary=summary,
        statistics=ContractStatistics(
            word_count=len(text.split()),
            clauses_detected=len(clauses),
            high_risk_clauses=sum(
                f.risk_level == "high" for f in findings
            ),
            critical_risk_clauses=sum(
                f.risk_level == "critical" for f in findings
            ),
        ),
        findings=findings,
        missing_clause_checks=_get_missing_checks(text),
        clause_classifications=classifications,
    )
