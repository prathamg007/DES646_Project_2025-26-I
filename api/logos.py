from transformers import pipeline, logging
import time
import numpy as np
from typing import List, Tuple, Dict
import core
import requests, re

def generate_sentence_pairs(sentences: List[str], mode: str = "adjacent") -> List[Tuple[str, str]]:
    """
    Generate premise-hypothesis sentence pairs for logical consistency checking.
    mode = 'adjacent' → (s1,s2), (s2,s3), ...
    mode = 'full' → all possible ordered pairs (s_i, s_j) with i < j
    """
    pairs = []
    if len(sentences) < 2:
        return pairs

    if mode == "adjacent":
        pairs = [(sentences[i], sentences[i + 1]) for i in range(len(sentences) - 1)]
    elif mode == "full":
        pairs = [(sentences[i], sentences[j]) for i in range(len(sentences)) for j in range(i + 1, len(sentences))]
    else:
        raise ValueError("mode must be 'adjacent' or 'full'")

    return pairs

def preprocess_logic_text(text: str) -> list[str]:
    """
    Adaptive preprocessing for logical consistency.
    - Detects syllogisms and merges relevant premises.
    - Otherwise returns standard sentence splits.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    cleaned = [s.strip() for s in sentences if len(s.strip()) > 2]
    merged = []
    i = 0
    while i < len(cleaned):
        s = cleaned[i]

        # 1. Merge syllogism-like premise → conclusion pairs
        if (
            i + 1 < len(cleaned)
            and re.search(r'\ball\b|\bevery\b|\bif\b', s, flags=re.I)
            and re.match(r'^[A-Z][a-z]+|He|She|They|It', cleaned[i + 1])
        ):
            merged.append(s + " " + cleaned[i + 1])
            i += 2
            continue

        # 2. Merge cause-effect (if ... then ...) statements
        if re.search(r'\bif\b.*\bthen\b', s, flags=re.I):
            merged.append(s)
            i += 1
            continue

        # 3. Fallback — keep sentence as-is
        merged.append(s)
        i += 1

    return merged

def enrich_with_conceptnet(text: str, limit_per_noun: int = 1) -> str:
    """
    Add simple ConceptNet 'IsA' relations for nouns/entities found in text.
    Returns the enriched text string.
    Example:
        Input: "Socrates is a man."
        Output: "Socrates is a man. Socrates is a human."
    """
    nouns = re.findall(r"\b[A-Z][a-z]+\b", text)
    added = []
    for n in nouns:
        try:
            url = f"https://api.conceptnet.io/query?node=/c/en/{n.lower()}&rel=/r/IsA&limit={limit_per_noun}"
            resp = requests.get(url, timeout=3).json()
            edges = resp.get("edges", [])
            for e in edges:
                end = e["end"]["label"]
                added.append(f"{n} is a {end}.")
        except Exception:
            continue
    if added:
        return text + " " + " ".join(added)
    return text

def compute_logical_coherence(text: str, nli_model=None, mode: str = "full", verbose: bool = False) -> float:
    """
    Compute an internal logical coherence score using NLI entailment.
    Score ∈ [0, 1] → 1 = consistent, 0 = contradictory.
    """
    logging.set_verbosity_error()
    if nli_model is None:
        nli_model = pipeline("text-classification", model="microsoft/deberta-large-mnli", top_k=None)

    expanded_text = enrich_with_conceptnet(text)

    sentences = preprocess_logic_text(expanded_text)  # whatever function you already have
    pairs = generate_sentence_pairs(sentences, mode='full')

    if not pairs:
        return 0.5  # neutral default

    entailment_sum, contradiction_sum = 0.0, 0.0

    for p, h in pairs:
        raw = nli_model(f"{p} </s></s> {h}")[0]
        probs = core.label_probs_from_pipeline_output(raw)
        p_entail = probs.get("ENTAILMENT", 0.0)
        p_contra = probs.get("CONTRADICTION", 0.0)
        entailment_sum += p_entail
        contradiction_sum += p_contra

        if verbose:
            print(f"{p[:50]} → {h[:50]} | entail={p_entail:.2f}, contra={p_contra:.2f}")

    avg_entail = entailment_sum / len(pairs)
    avg_contra = contradiction_sum / len(pairs)
    raw_score = avg_entail - avg_contra
    norm_score = (raw_score + 1) / 2  # normalize to [0,1]
    return round(float(norm_score), 4)

if __name__ == '__main__':
    texts = [
        {
            "name": "Fully logical chain",
            "text": "All humans are mortal. Therefore, Socrates is mortal."
        },
        {
            "name": "Contradictory logic",
            "text": "The sky is blue. The sky is not blue."
        },
        {
            "name": "Neutral / disconnected sentences",
            "text": "The cat sat on the mat. The Eiffel Tower is in Paris."
        }
    ]

    for t in texts:
        print(f"\n=== {t['name']} ===")
        print(f"{t['text']}")
        score = compute_logical_coherence(t["text"])
        print("Logos (Logical Consistency) Score:", score)