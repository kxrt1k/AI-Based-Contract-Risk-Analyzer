
import re
from .schemas import Finding


RULES = [
    (
        "unilateral_termination",
        r"\b(?:may|can|shall be entitled to|has the right to)\s+terminate\b"
        r"|\bterminate\b.{0,100}\b(?:without cause|for convenience|at any time)\b"
        r"|\btermination for convenience\b",
        "high",
        0.78,
        "A termination right may allow a party to exit the agreement.",
        "Check which party holds the right, notice periods, cure rights, and termination fees.",
    ),
    (
        "indemnity",
        r"\bindemnif(?:y|ies|ied|ication)\b",
        "medium",
        0.65,
        "An indemnity obligation is present; its scope may affect financial exposure.",
        "Review covered claims, fault standards, defence control, caps, and exclusions.",
    ),
    (
        "uncapped_liability",
        r"\b(?:unlimited liability|without limitation|no limitation of liability|"
        r"liability shall not be limited|liability is not capped)\b",
        "high",
        0.72,
        "The clause may describe liability that is not limited.",
        "Check the full liability clause, exceptions, applicable caps, and mutuality.",
    ),
    (
        "liability_cap",
        r"\b(?:total|aggregate|maximum|overall)\s+liability\b.{0,180}"
        r"\b(?:shall not exceed|will not exceed|limited to|capped at|"
        r"shall be limited to|is limited to)\b"
        r"|\bliability\b.{0,100}\b(?:shall not exceed|will not exceed|"
        r"limited to|capped at)\b",
        "medium",
        0.78,
        "A liability cap appears to be present.",
        "Verify the cap amount, exclusions, time period, covered claims, and mutuality.",
    ),
    (
        "payment",
        r"\b(?:payment terms?|pay|invoice|invoicing|late fee|late payment|"
        r"interest on overdue|payment due|non-refundable)\b",
        "medium",
        0.62,
        "Payment terms may create financial obligations or penalties.",
        "Verify amounts, due dates, dispute rights, taxes, and refund terms.",
    ),
    (
        "confidentiality",
        r"\b(?:confidential information|confidentiality|non-disclosure|"
        r"nondisclosure)\b",
        "low",
        0.60,
        "Confidentiality language is present; scope and duration need review.",
        "Review exclusions, permitted disclosures, duration, and return/deletion duties.",
    ),
    (
        "intellectual_property",
        r"\b(?:assigns?|assignment of|work product|intellectual property|"
        r"ownership of deliverables)\b",
        "medium",
        0.64,
        "The text addresses intellectual property or ownership.",
        "Confirm background IP, new IP, licences, third-party materials, and transfer conditions.",
    ),
    (
        "data_protection",
        r"\b(?:personal data|data protection|security incident|data breach|"
        r"privacy)\b",
        "medium",
        0.62,
        "The text addresses data handling or security.",
        "Review roles, purposes, security, breach notification, subprocessors, and deletion.",
    ),
    (
        "automatic_renewal",
        r"\b(?:automatically renew|automatic renewal|renewal term)\b",
        "medium",
        0.63,
        "Automatic renewal may extend obligations unless notice is given on time.",
        "Check renewal length, opt-out deadline, notice method, and price changes.",
    ),
    (
        "dispute_resolution",
        r"\b(?:arbitration|exclusive jurisdiction|governing law|"
        r"venue for any dispute|dispute resolution)\b",
        "low",
        0.60,
        "The clause may determine the forum or rules used to resolve disputes.",
        "Confirm governing law, venue, costs, rules, and enforceability.",
    ),
]


WEIGHT = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def detect_findings(clauses: list[str]) -> list[Finding]:
    findings = []
    seen = set()

    for clause in clauses:
        for category, pattern, level, confidence, reason, recommendation in RULES:
            match = re.search(pattern, clause, re.IGNORECASE)
            if not match:
                continue

            evidence = re.sub(r"\s+", " ", clause).strip()
            key = (category, evidence[:240].lower())

            if key in seen:
                continue

            seen.add(key)

            findings.append(
                Finding(
                    clause_type=category,
                    risk_level=level,
                    confidence=confidence,
                    evidence=evidence[:700],
                    reason=reason,
                    recommendation=recommendation,
                    source="rules",
                )
            )

    return findings


def missing_clause_checks(text: str) -> list[str]:
    lower = text.lower()

    checks = [
        (
            "termination",
            r"\b(?:terminat\w*|expiry|expiration|expire)\b",
            "No obvious termination wording detected; verify whether exit rights are addressed.",
        ),
        (
            "liability",
            r"\b(?:liability|liable|limitation of liability|indemnif\w*)\b",
            "No obvious liability or indemnity wording detected; verify caps and exclusions.",
        ),
        (
            "confidentiality",
            r"\b(?:confidentiality|confidential information|non-disclosure|nondisclosure)\b",
            "No obvious confidentiality wording detected; verify disclosure rules.",
        ),
        (
            "dispute",
            r"\b(?:dispute resolution|arbitration|governing law|jurisdiction|venue)\b",
            "No obvious dispute-resolution or governing-law wording detected.",
        ),
        (
            "payment",
            r"\b(?:payment|invoice|invoicing|fees|payable|price)\b",
            "No obvious payment wording detected; verify fees, invoicing, and due dates.",
        ),
    ]

    return [
        message
        for _, pattern, message in checks
        if not re.search(pattern, lower, re.IGNORECASE)
    ]
