import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from transformers import pipeline, logging
import time
import core


# -----------------------------
# Factual Consistency (Ethos)
# -----------------------------
def compute_factual_consistency(source_text: str, candidate_text: str, nli_model=None) -> float:
    """
    Compute factual consistency score between source and candidate.
    """
    core.suppress_transformers_warnings()
    if nli_model is None:
        nli_model = pipeline("text-classification", model="roberta-large-mnli", top_k=None)

    src_sents = core.split_sentences(source_text)
    cand_sents = core.split_sentences(candidate_text)

    if not src_sents or not cand_sents:
        return 0.0

    pair_scores = []
    for cand in cand_sents:
        for src in src_sents:
            output = nli_model(f"{cand} </s></s> {src}")[0]
            probs = core.label_probs_from_pipeline_output(output)
            score, _ = core.pair_score_from_probs(probs)
            pair_scores.append(score)

    return float(np.mean(pair_scores))


# -----------------------------
# Formality
# -----------------------------
def compute_formality(text: str, formality_model=None, verbose: bool = False) -> float:
    """
    Compute an average formality score (0 to 1) using the pretrained formality ranker.
    Higher → more formal writing.
    Automatically inverts scores for 'informal' predictions.
    """
    if formality_model is None:
        formality_model = pipeline(
            "text-classification",
            model="s-nlp/roberta-base-formality-ranker",
            top_k=1
        )

    sentences = core.split_sentences(text)
    if not sentences:
        return 0.0

    scores = []
    for s in sentences:
        result = formality_model(s)[0][0]
        label = result["label"].lower()
        score = float(result["score"])

        # Invert if the predicted label is 'informal'
        if label == "informal":
            score = 1 - score

        score = max(0.0, min(1.0, score))
        scores.append(score)

        if verbose:
            print(f"[{label}] {s} → adjusted_score={score:.3f}")

    return float(np.mean(scores))


# -----------------------------
# Combined Evaluation
# -----------------------------
def analyze_ethos_formality(source: str, candidate: str):
    start = time.time()
    print("---- Ethos & Formality Evaluation ----")
    print("Source:", source)
    print("Candidate:", candidate)
    print("--------------------------------------")

    ethos_score = compute_factual_consistency(source, candidate)
    formality_score = compute_formality(candidate)
    elapsed = core.elapsed_time(start)

    print(f"Ethos (Factual Consistency) Score: {ethos_score:.3f}")
    print(f"Formality Score: {formality_score:.3f}")
    print(f"Runtime: {elapsed} s")
    return (0.6*ethos_score+0.4*formality_score,ethos_score, formality_score)


# -----------------------------
# Example test cases
# -----------------------------
if __name__ == "__main__":
    tests = [
        {
            "name": "Highly consistent & formal",
            "source": "The Eiffel Tower is located in Paris. It was completed in 1889.",
            "candidate": "The Eiffel Tower, situated in Paris, was completed in 1889."
        },
        {
            "name": "Consistent but informal",
            "source": "The Eiffel Tower is located in Paris. It was completed in 1889.",
            "candidate": "Yeah, that big tower in Paris was built in 1889!"
        },
        {
            "name": "Inconsistent & informal",
            "source": "The Eiffel Tower is located in Paris. It was completed in 1889.",
            "candidate": "The Eiffel Tower is in London, dude!"
        }
    ]

    for t in tests:
        print(f"\n=== Test: {t['name']} ===")
        result = analyze_ethos_formality(t["source"], t["candidate"])
        print("Expected trends:")
        print(" - High factual consistency → Ethos near 1.0")
        print(" - Informal tone → Formality near 0.2–0.4")
        print(" - Formal tone → Formality near 0.8–1.0")
        print(result)