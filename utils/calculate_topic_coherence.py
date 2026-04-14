"""
Calculate topic coherence scores (C_v and U_MASS) without gensim.

Implements the coherence metrics from:
  - Röder et al. (2015): "Exploring the Space of Topic Coherence Measures"
  - Mimosa et al. (with gensim's CoherenceModel)

C_v: Uses normalized pointwise mutual information (NPMI) of top word pairs,
     segmented into sliding windows. Higher = more coherent.
U_MASS: Uses document co-occurrence of top word pairs. Higher = more coherent.

Usage:
    # First, export beta from R:
    Rscript utils/export_lda_beta.R

    # Then, calculate coherence:
    uv run python utils/calculate_topic_coherence.py
"""

import json
import math
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

# === Config ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "overture_pois"
BETA_DIR = DATA_DIR / "lda_beta"

K_VALUES = [4, 5, 6, 7, 8]
TOP_N_WORDS = 20  # Number of top words for coherence calculation
WINDOW_SIZE = 10  # Sliding window size for C_v


def load_documents_and_vocabulary() -> tuple:
    """Load station-POI documents and vocabulary from station_poi_counts.csv."""
    counts_path = DATA_DIR / "station_poi_counts.csv"

    if not counts_path.exists():
        raise FileNotFoundError(
            f"Station POI counts not found: {counts_path}\n"
            "Please run the LDA pipeline first."
        )

    print(f"Loading station POI counts from {counts_path}...")
    df = pd.read_csv(counts_path)

    # station_code is the first column, rest are POI categories
    if "station_code" in df.columns:
        df = df.set_index("station_code")

    # Get vocabulary (POI class names)
    vocab = list(df.columns)

    # Convert to list of documents (each document is a list of POI class words)
    # Repeat each POI class according to its count (like a bag-of-words)
    documents = []
    for station in df.index:
        row = df.loc[station]
        doc = []
        for poi_class, count in row.items():
            if count > 0:
                doc.extend([poi_class] * int(count))
        documents.append(doc)

    print(f"  Loaded {len(documents)} documents (stations)")
    print(f"  Vocabulary size: {len(vocab)}")

    return documents, vocab


def load_beta_matrix(k: int) -> tuple:
    """Load beta matrix from CSV exported by R."""
    beta_path = BETA_DIR / f"beta_k{k}.csv"

    if not beta_path.exists():
        raise FileNotFoundError(f"Beta matrix not found: {beta_path}")

    beta_df = pd.read_csv(beta_path, index_col=0)
    beta = beta_df.values
    beta_vocab = list(beta_df.columns)

    print(f"  Loaded beta K={k}: {beta.shape[0]} topics x {beta.shape[1]} words")
    return beta, beta_vocab


def get_top_words(beta: np.ndarray, vocab: list, top_n: int = TOP_N_WORDS) -> list:
    """Get top N words for each topic from beta matrix."""
    top_words = []
    for topic_idx in range(beta.shape[0]):
        top_indices = beta[topic_idx, :].argsort()[-top_n:][::-1]
        top_words.append([vocab[i] for i in top_indices])
    return top_words


def compute_segmented_document_windows(documents: list, window_size: int = WINDOW_SIZE) -> list:
    """
    Segment each document into overlapping windows of size window_size.
    Each window is treated as a 'pseudo-document' for co-occurrence counting.
    """
    windows = []
    for doc in documents:
        # Pad short documents (repeat the document to reach window_size)
        if len(doc) < window_size:
            padded = doc * (window_size // len(doc) + 1)
            padded = padded[:window_size]
            windows.append(padded)
        else:
            # Slide window of size window_size across document
            for i in range(len(doc) - window_size + 1):
                windows.append(doc[i:i + window_size])
    return windows


def compute_confirmation_measures(windows: list, top_words: list, vocab: list) -> dict:
    """
    Compute C_v confirmation measure using NPMI on segmented windows.

    For each topic's top words, compute:
      C_v = mean of NPMI(w_i, w_j) for all word pairs (w_i, w_j)
      where NPMI(w_i, w_j) = log(P(w_i, w_j) * |V| / (P(w_i) * P(w_j))) / (-log(P(w_i, w_j)))
    """
    # Count word frequencies and co-occurrences across all windows
    word_freq = Counter()
    word_pair_freq = defaultdict(int)
    total_windows = len(windows)

    for window in windows:
        unique_words = set(window)
        for w in unique_words:
            word_freq[w] += 1
        for w1, w2 in combinations(sorted(unique_words), 2):
            word_pair_freq[(w1, w2)] += 1

    # For each topic, compute C_v
    topic_coherences = []
    topic_details = []

    for topic_idx, words in enumerate(top_words):
        npmi_values = []
        for w1, w2 in combinations(words, 2):
            # Ensure consistent ordering for lookup
            pair = tuple(sorted([w1, w2]))

            p_w1 = word_freq[w1] / total_windows if word_freq[w1] > 0 else 1e-10
            p_w2 = word_freq[w2] / total_windows if word_freq[w2] > 0 else 1e-10
            p_w1w2 = word_pair_freq[pair] / total_windows

            if p_w1w2 == 0:
                # No co-occurrence: NPMI = -1 (worst case)
                npmi = -1.0
            else:
                # NPMI formula
                numerator = math.log(p_w1w2 / (p_w1 * p_w2) + 1e-10)
                denominator = -math.log(p_w1w2)
                npmi = numerator / denominator

            # Clamp to [-1, 1]
            npmi = max(-1.0, min(1.0, npmi))
            npmi_values.append(npmi)

        topic_cv = np.mean(npmi_values)
        topic_coherences.append(topic_cv)
        topic_details.append({
            "topic": topic_idx + 1,
            "cv": round(topic_cv, 4),
            "n_word_pairs": len(npmi_values),
            "mean_npmi": round(np.mean(npmi_values), 4)
        })

    return {
        "cv": np.mean(topic_coherences),
        "per_topic": topic_details
    }


def compute_umass_coherence(documents: list, top_words: list) -> float:
    """
    Compute U_MASS coherence: log(P(w_j | w_i)) for consecutive word pairs.

    U_MASS = (2 / (W*(W-1))) * sum_{i<j} log(D(w_i, w_j) + 1 / D(w_i))
    where D(w_i, w_j) = number of documents containing both w_i and w_j
    and D(w_i) = number of documents containing w_i.
    """
    # Pre-compute document frequencies
    doc_freq = Counter()
    doc_pair_freq = defaultdict(int)

    for doc in documents:
        doc_words = set(doc)
        for w in doc_words:
            doc_freq[w] += 1
        for w1, w2 in combinations(sorted(doc_words), 2):
            doc_pair_freq[(w1, w2)] += 1

    # For each topic, compute U_MASS
    topic_umass_values = []

    for words in top_words:
        log_probs = []
        for i in range(len(words) - 1):
            w1 = words[i]
            w2 = words[i + 1]
            pair = tuple(sorted([w1, w2]))

            d_wi = doc_freq[w1] if doc_freq[w1] > 0 else 1
            d_wi_wj = doc_pair_freq[pair] if pair in doc_pair_freq else 0

            # log((D(wi, wj) + 1) / D(wi))
            log_prob = math.log((d_wi_wj + 1) / d_wi)
            log_probs.append(log_prob)

        topic_umass_values.append(np.mean(log_probs))

    return np.mean(topic_umass_values)


def main():
    print("=" * 60)
    print("Topic Coherence Calculation (pure Python, no gensim)")
    print("=" * 60)

    # Load documents and vocabulary
    documents, vocab = load_documents_and_vocabulary()

    # Check beta directory
    if not BETA_DIR.exists():
        print(f"\nERROR: Beta directory not found: {BETA_DIR}")
        print("Please run: Rscript utils/export_lda_beta.R")
        return

    # Pre-compute segmented windows for C_v
    print(f"\nSegmenting documents (window_size={WINDOW_SIZE})...")
    windows = compute_segmented_document_windows(documents, WINDOW_SIZE)
    print(f"  Created {len(windows)} windows")

    results = {}

    for k in K_VALUES:
        print(f"\n{'='*40}")
        print(f"K={k}")
        print(f"{'='*40}")

        try:
            # Load beta matrix
            beta, beta_vocab = load_beta_matrix(k)

            # Reorder beta columns to match DTM vocabulary if needed
            if beta_vocab != vocab:
                print(f"  Vocabulary mismatch — reordering beta columns...")
                vocab_to_idx = {v: i for i, v in enumerate(beta_vocab)}
                beta_reordered = np.zeros((beta.shape[0], len(vocab)))
                matched = 0
                for i, v in enumerate(vocab):
                    if v in vocab_to_idx:
                        beta_reordered[:, i] = beta[:, vocab_to_idx[v]]
                        matched += 1
                beta = beta_reordered
                print(f"  Matched {matched}/{len(vocab)} vocabulary terms")

            # Get top words
            top_words = get_top_words(beta, vocab, TOP_N_WORDS)

            print(f"  Top words per topic:")
            for i, words in enumerate(top_words):
                print(f"    Topic {i+1}: {', '.join(words[:8])}...")

            # Compute C_v coherence
            cv_result = compute_confirmation_measures(windows, top_words, vocab)
            cv_score = cv_result["cv"]

            # Compute U_MASS coherence
            umass_score = compute_umass_coherence(documents, top_words)

            print(f"\n  C_v coherence:    {cv_score:.4f}")
            print(f"  U_MASS coherence: {umass_score:.4f}")

            for detail in cv_result["per_topic"]:
                print(f"    Topic {detail['topic']}: C_v={detail['cv']:.4f} "
                      f"({detail['n_word_pairs']} pairs)")

            results[f"k{k}"] = {
                "k": k,
                "coherence_cv": round(cv_score, 4),
                "coherence_umass": round(umass_score, 4)
            }

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Save results
    output_path = DATA_DIR / "coherence_scores_gensim.json"
    output_data = {}
    for key, result in results.items():
        output_data[key] = {
            "k": result["k"],
            "coherence_cv": result["coherence_cv"],
            "coherence_umass": result["coherence_umass"]
        }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}")

    if results:
        sorted_cv = sorted(results.values(), key=lambda x: x["coherence_cv"], reverse=True)

        print("\nCoherence Scores (higher is better for both):")
        for r in sorted_cv:
            print(f"  K={r['k']}: C_v={r['coherence_cv']:.4f}, U_MASS={r['coherence_umass']:.4f}")

        optimal_k = sorted_cv[0]["k"]
        print(f"\nOptimal K by C_v coherence: {optimal_k}")

        # Also show by U_MASS
        sorted_umass = sorted(results.values(), key=lambda x: x["coherence_umass"], reverse=True)
        optimal_k_umass = sorted_umass[0]["k"]
        print(f"Optimal K by U_MASS coherence: {optimal_k_umass}")

    print(f"\nSaved results to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
