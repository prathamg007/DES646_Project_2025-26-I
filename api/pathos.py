# pathos.py

import time
import numpy as np
from transformers import pipeline, logging
import core
from typing import List, Dict


# -----------------------------
# Emotion / Pathos computation
# -----------------------------
def compute_emotion_scores(text: str, emotion_model=None, verbose: bool = False) -> Dict[str, float]:
    """
    Compute emotion distribution for input text.
    Returns dict: emotion label → average score across sentences.
    """
    from collections import defaultdict
    logging.set_verbosity_error()
    if emotion_model is None:
        emotion_model = pipeline(
            "text-classification",
            model="bhadresh-savani/distilbert-base-uncased-emotion",
            top_k=None
        )

    sentences = core.split_sentences(text)
    if not sentences:
        return {}

    # Use defaultdict to handle unexpected labels dynamically
    all_scores = defaultdict(float)

    for s in sentences:
        results = emotion_model(s)[0]  # list of dicts
        for r in results:
            label = r["label"].lower()
            score = float(r["score"])
            all_scores[label] += score
        if verbose:
            print(f"[DEBUG] Sentence: {s}")
            print({r["label"]: round(r["score"],3) for r in results})

    # Average across sentences
    num_sents = len(sentences)
    averaged_scores = {k: v / num_sents for k, v in all_scores.items()}

    return averaged_scores


def compute_pathos_score(text: str, emotion_model=None) -> float:
    """
    Convert emotion distribution to a single Pathos score ∈ [0,1].
    Idea: Positive emotions (joy, surprise) increase persuasiveness,
    negative/neutral decrease it.
    """
    scores = compute_emotion_scores(text, emotion_model)
    if not scores:
        return 0.5

    pos = scores.get("joy", 0.0) + scores.get("surprise", 0.0)
    neg = scores.get("anger", 0.0) + scores.get("fear", 0.0) + scores.get("disgust", 0.0)
    neutral = scores.get("neutral", 0.0)
    # pathos ∈ [0,1]
    raw = pos - (neg + 0.5*neutral)
    norm = (raw + 1) / 2  # rough normalization
    return round(float(max(0.0, min(1.0, norm))), 4)


# -----------------------------
# Combined Pathos Analysis
# -----------------------------
def analyze_pathos(text: str, emotion_model=None):
    start = time.time()
    print("---- Pathos (Emotional Appeal) Evaluation ----")
    print("Text:", text)
    print("----------------------------------------------")
    scores = compute_emotion_scores(text, emotion_model, verbose=True)
    pathos_score = compute_pathos_score(text, emotion_model)
    elapsed = round(time.time() - start, 2)

    print("Emotion Scores:", {k: round(v,3) for k,v in scores.items()})
    print("Pathos Score:", pathos_score)
    print(f"Runtime: {elapsed} s")
    return {"emotion_scores": scores, "pathos_score": pathos_score, "runtime": elapsed}


# -----------------------------
# Example Test Cases
# -----------------------------
if __name__ == "__main__":
    tests = [
        {
            "name": "Highly positive / inspiring",
            "text": "I can’t believe how inspiring your story was — it gave me hope!"
        },
        {
            "name": "Neutral / factual",
            "text": "The Eiffel Tower is located in Paris. It was completed in 1889."
        },
        {
            "name": "Angry / negative",
            "text": "I am furious that this happened. It's absolutely unacceptable!"
        }
    ]

    for t in tests:
        print(f"\n=== Test: {t['name']} ===")
        analyze_pathos(t["text"])