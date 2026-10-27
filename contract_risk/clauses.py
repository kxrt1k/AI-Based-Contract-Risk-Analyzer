
import re


# Common abbreviations that should not normally end a sentence.
_ABBREVIATIONS = re.compile(
    r"\b(?:Mr|Mrs|Ms|Dr|Prof|Inc|Ltd|Corp|No|Nos|e\.g|i\.e|etc)\.$",
    re.IGNORECASE,
)


def _split_sentences(text: str) -> list[str]:
    """Split ordinary text into sentences without splitting common abbreviations."""
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'])', text)
    sentences = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Join a fragment back to the preceding sentence if the preceding
        # sentence ends with a known abbreviation.
        if sentences and _ABBREVIATIONS.search(sentences[-1]):
            sentences[-1] += " " + part
        else:
            sentences.append(part)

    return sentences


def split_clauses(text: str) -> list[str]:
    """Split contract text into usable clause-sized pieces."""
    if not isinstance(text, str) or not text.strip():
        return []

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized).strip()

    # First split at blank lines, which usually mark clause boundaries.
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n+", normalized)
        if paragraph.strip()
    ]

    clauses = []

    for paragraph in paragraphs:
        # Separate numbered or lettered clause headings where possible.
        numbered_parts = re.split(
            r"\s+(?=(?:\d+(?:\.\d+)*[.)]?|[A-Z][.)])\s+)",
            paragraph,
        )

        for part in numbered_parts:
            part = part.strip()
            if not part:
                continue

            # Keep normal-sized paragraphs together. Split long, single-line
            # blocks into sentences so the classifier does not receive an
            # entire contract as one input.
            if len(part) > 1200:
                clauses.extend(_split_sentences(part))
            else:
                clauses.extend(_split_sentences(part))

    # Remove empty pieces and duplicate whitespace.
    cleaned = []
    for clause in clauses:
        clause = re.sub(r"\s+", " ", clause).strip()
        if clause:
            cleaned.append(clause)

    return cleaned
