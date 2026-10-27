
import os
from functools import lru_cache
from pathlib import Path


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "artifacts"
    / "legalbert-clause-classifier"
)


@lru_cache(maxsize=1)
def _pipeline():
    """Load the trained clause classifier once and reuse it."""
    model_path = Path(
        os.getenv("CONTRACT_RISK_MODEL", str(DEFAULT_MODEL_PATH))
    ).expanduser()

    if not model_path.exists():
        return None

    try:
        import torch
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError(
            "Model dependencies are missing. Activate your virtual "
            "environment and install the project's training dependencies."
        ) from exc

    if not (model_path / "config.json").exists():
        raise RuntimeError(
            f"Model configuration not found in: {model_path}"
        )

    device = 0 if torch.cuda.is_available() else -1

    return pipeline(
        task="text-classification",
        model=str(model_path),
        tokenizer=str(model_path),
        device=device,
        truncation=True,
    )


def classify_clause(text: str):
    """Return a clause category and model confidence, or None if unavailable."""
    if not isinstance(text, str) or not text.strip():
        return None

    pipe = _pipeline()

    if pipe is None:
        return None

    prediction = pipe(text[:12000])[0]

    return {
        "label": str(prediction["label"]),
        "score": float(prediction["score"]),
    }
