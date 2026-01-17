"""
final.py
CLI + modular interface for analyzing a text for Ethos, Logos, Pathos.

Dependencies:
 - ethos.py
 - logos.py
 - pathos.py
"""
import os
import argparse
import json
import ethos
import logos
import pathos


# -----------------------------
# Aggregate scoring functions
# -----------------------------
def compute_ethos_score(source_text: str, candidate_text: str, nli_model=None, formality_model=None):
    """
    Weighted Ethos: 0.6 factual_consistency + 0.4 formality
    """
    factual = ethos.compute_factual_consistency(source_text, candidate_text, nli_model=nli_model)
    formal = ethos.compute_formality(candidate_text, formality_model=formality_model)
    score = 0.6 * factual + 0.4 * formal
    return round(score, 4), factual, formal


def compute_logos_score(text: str, nli_model=None):
    """
    Internal logical coherence score from logos module
    """
    return logos.compute_logical_coherence(text, nli_model=nli_model)


def compute_pathos_score(text: str, emotion_model=None):
    """
    Returns average emotional appeal score (0..1)
    """
    return pathos.compute_pathos_score(text, emotion_model=emotion_model)


# -----------------------------
# Full analysis function
# -----------------------------
def analyze_text(source_text: str, candidate_text: str):
    """
    Returns a dictionary with ethos, logos, pathos scores
    """
    result = {}
    ethos_score, factual, formal = compute_ethos_score(source_text, candidate_text)
    logos_score = compute_logos_score(candidate_text)
    pathos_score = compute_pathos_score(candidate_text)

    result["ethos"] = {
        "score": ethos_score,
        "factual_consistency": round(factual, 4),
        "formality": round(formal, 4)
    }
    result["logos"] = round(logos_score, 4)
    result["pathos"] = round(pathos_score, 4)
    return result

def analyze_text_sentencewise(source_text: str, candidate_text: str):
    """
    Returns a dictionary with:
    - overall scores
    - sentence-wise breakdown for each sentence in candidate_text
    """
    sentences = ethos.core.split_sentences(candidate_text)
    sentence_results = []

    for sent in sentences:
        ethos_score, factual, formal = ethos.analyze_ethos_formality(source_text, sent)
        logos_score = logos.compute_logical_coherence(sent)
        pathos_score = pathos.compute_pathos_score(sent)

        sentence_results.append({
            "sentence": sent,
            "ethos": {
                "score": ethos_score,
                "factual_consistency": round(factual, 4),
                "formality": round(formal, 4)
            },
            "logos": round(logos_score, 4),
            "pathos": round(pathos_score, 4)
        })

    # Compute overall scores for candidate text
    overall = {}

    # Compute averages for ethos subcomponents
    avg_ethos_score = sum(r["ethos"]["score"] for r in sentence_results) / len(sentence_results)
    avg_factual = sum(r["ethos"]["factual_consistency"] for r in sentence_results) / len(sentence_results)
    avg_formal = sum(r["ethos"]["formality"] for r in sentence_results) / len(sentence_results)

    # Add overall ethos, logos, pathos
    overall["ethos"] = {
        "score": round(avg_ethos_score, 4),
        "factual_consistency": round(avg_factual, 4),
        "formality": round(avg_formal, 4)
    }
    overall["logos"] = round(sum(r["logos"] for r in sentence_results) / len(sentence_results), 4)
    overall["pathos"] = round(sum(r["pathos"] for r in sentence_results) / len(sentence_results), 4)

    return {
        "overall": overall,
        "sentencewise": sentence_results
    }



# -----------------------------
# CLI interface
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Analyze text for Ethos, Logos, Pathos")
    parser.add_argument("input_file", nargs="?", default="default.txt", help="Input text file")
    parser.add_argument("-o", "--output", default="output.txt", help="Output file to save analysis")
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    # For simplicity, we use the same text as source and candidate (can be changed)
    analysis = analyze_text(text, text)

    # Write output
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=4)

    print(f"Analysis saved to {args.output}")
    print(json.dumps(analysis, indent=4))

# -----------------------------
# Default testability
# -----------------------------
if __name__ == "__main__":
    # If default.txt does not exist, create a sample input
    if not os.path.exists("default.txt"):
        sample_text = (
            "The Eiffel Tower is located in Paris and was completed in 1889. "
            "It is one of the most famous landmarks in the world. "
            "Visiting it gives tourists immense joy and inspiration."
        )
        with open("default.txt", "w", encoding="utf-8") as f:
            f.write(sample_text)

    main()