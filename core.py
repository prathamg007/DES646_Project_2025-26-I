# core.py
import spacy
import nltk
from nltk.tokenize import sent_tokenize
from typing import List, Dict, Tuple
from transformers import logging
import time
from collections import defaultdict

# -----------------------------
# Sentence splitting utilities
# -----------------------------
def _split_sentences_spacy(text: str) -> List[str]:
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

def _split_sentences_nltk(text: str) -> List[str]:
    nltk.download("punkt", quiet=True)
    return [s.strip() for s in sent_tokenize(text) if s.strip()]

def split_sentences(text: str) -> List[str]:
    """Try spaCy first, fallback to NLTK."""
    try:
        return _split_sentences_spacy(text)
    except Exception:
        return _split_sentences_nltk(text)

# -----------------------------
# NLI helpers
# -----------------------------
def label_probs_from_pipeline_output(entry: List[Dict[str, float]]) -> Dict[str, float]:
    """Convert pipeline outputs to dict of label → prob."""
    return {x["label"].upper(): float(x["score"]) for x in entry}

def pair_score_from_probs(probs: Dict[str, float]) -> Tuple[float, str]:
    """
    Convert label probabilities into a single support score in [0,1].
    Heuristic: pair_score = p_entail + 0.5 * p_neutral
    Returns score and dominant label.
    """
    p_entail = probs.get("ENTAILMENT", 0.0)
    p_neutral = probs.get("NEUTRAL", 0.0)
    pair_score = p_entail + 0.5 * p_neutral
    dominant_label = max(probs, key=probs.get)
    return pair_score, dominant_label

# -----------------------------
# Timing helper
# -----------------------------
def elapsed_time(t0: float) -> float:
    return round(time.time() - t0, 3)

# -----------------------------
# Default dict helper for dynamic labels
# -----------------------------
def dynamic_label_dict() -> defaultdict:
    return defaultdict(float)

# -----------------------------
# Transformers logging silence
# -----------------------------
def suppress_transformers_warnings():
    logging.set_verbosity_error()