"""
Calculate topic coherence scores using gensim's CoherenceModel.

This script loads beta matrices exported from R LDA models and computes
the C_v coherence metric for each K value.

Usage:
    # First, export beta from R:
    Rscript utils/export_lda_beta.R

    # Then, calculate coherence:
    python utils/calculate_topic_coherence_gensim.py
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from gensim.models import CoherenceModel
from gensim.corpora import Dictionary

# === Config ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "overture_pois"
BETA_DIR = DATA_DIR / "lda_beta"

K_VALUES = [4, 5, 6, 7, 8]
TOP_N_WORDS = 20  # Number of top words for coherence calculation


def load_documents_and_vocabulary() -> tuple:
    """Load station-POI documents and vocabulary."""
    counts_path = DATA_DIR / "station_poi_counts.csv"

    if not counts_path.exists():
        raise FileNotFoundError(
            f"Station POI counts not found: {counts_path}\n"
            "Please run the LDA pipeline first."
        )

    print(f"Loading station POI counts from {counts_path}...")
    df = pd.read_csv(counts_path)
    df = df.set_index("station_code")

    # Get vocabulary (POI class names)
    vocab = [col for col in df.columns if col != "station_code"]

    # Convert to list of documents (each document is a list of words/POI classes)
    # For LDA coherence, we need documents as word lists, not counts
    documents = []
    for station in df.index:
        row = df.loc[station]
        # Repeat each POI class according to its count
        doc = []
        for poi_class, count in row.items():
            if count > 0:
                doc.extend([poi_class] * int(count))
        documents.append(doc)

    print(f"  Loaded {len(documents)} documents (stations)")
    print(f"  Vocabulary size: {len(vocab)}")

    return documents, vocab


def load_beta_matrix(k: int) -> np.ndarray:
    """Load beta matrix from CSV exported by R."""
    beta_path = BETA_DIR / f"beta_k{k}.csv"

    if not beta_path.exists():
        raise FileNotFoundError(
            f"Beta matrix not found: {beta_path}\n"
            f"Please run: Rscript utils/export_lda_beta.R"
        )

    print(f"  Loading beta from {beta_path}...")
    beta_df = pd.read_csv(beta_path, index_col=0)
    beta = beta_df.values

    print(f"    Beta shape: {beta.shape} (topics x words)")

    return beta, list(beta_df.columns)


def get_top_words_from_beta(beta: np.ndarray, vocab: list, top_n: int = TOP_N_WORDS) -> list:
    """Get top N words for each topic from beta matrix."""
    top_words = []

    for topic_idx in range(beta.shape[0]):
        # Get indices of top words by probability
        top_indices = beta[topic_idx, :].argsort()[-top_n:][::-1]
        top_words_for_topic = [vocab[i] for i in top_indices]
        top_words.append(top_words_for_topic)

    return top_words


def calculate_coherence_with_gensim(documents: list, vocab: list, beta: np.ndarray, k: int) -> dict:
    """
    Calculate topic coherence using gensim's CoherenceModel.

    Args:
        documents: List of documents (each is a list of words)
        vocab: Vocabulary list
        beta: Beta matrix from R LDA model (topics x words)
        k: Number of topics

    Returns:
        Dictionary with coherence metrics
    """
    print(f"\nCalculating coherence for K={k}...")

    # Get top words for each topic
    top_words = get_top_words_from_beta(beta, vocab, TOP_N_WORDS)

    # Create dictionary from documents
    dictionary = Dictionary(documents)

    # Create CoherenceModel
    # u_mass: Requires top_words as list of list of strings
    # c_v: Requires documents and dictionary
    coherence_model = CoherenceModel(
        topics=top_words,
        texts=documents,
        dictionary=dictionary,
        coherence="c_v",  # C_v coherence (recommended)
        topn=TOP_N_WORDS
    )

    coherence = coherence_model.get_coherence()

    # Also calculate u_mass for comparison
    coherence_umass_model = CoherenceModel(
        topics=top_words,
        texts=documents,
        dictionary=dictionary,
        coherence="u_mass",
        topn=TOP_N_WORDS
    )
    coherence_umass = coherence_umass_model.get_coherence()

    result = {
        "k": k,
        "coherence_cv": round(coherence, 4),
        "coherence_umass": round(coherence_umass, 4),
        "top_words": top_words
    }

    print(f"  C_v coherence: {coherence:.4f}")
    print(f"  U_MASS coherence: {coherence_umass:.4f}")

    return result


def main():
    """Main execution."""
    print("="*60)
    print("Topic Coherence Calculation (gensim)")
    print("="*60)

    # Load documents and vocabulary
    documents, vocab = load_documents_and_vocabulary()

    # Check if beta directory exists
    if not BETA_DIR.exists():
        print("\nERROR: Beta directory not found!")
        print(f"  Expected: {BETA_DIR}")
        print(f"  Please run: Rscript utils/export_lda_beta.R")
        return

    results = {}

    for k in K_VALUES:
        try:
            # Load beta matrix
            beta, beta_vocab = load_beta_matrix(k)

            # Verify vocabulary matches
            if beta_vocab != vocab:
                print(f"  WARNING: Vocabulary mismatch!")
                print(f"    Beta vocab: {len(beta_vocab)} words")
                print(f"    DTM vocab: {len(vocab)} words")
                # Reorder beta to match DTM vocab if needed
                vocab_to_idx = {v: i for i, v in enumerate(beta_vocab)}
                beta_reordered = np.zeros((beta.shape[0], len(vocab)))
                for i, v in enumerate(vocab):
                    if v in vocab_to_idx:
                        beta_reordered[:, i] = beta[:, vocab_to_idx[v]]
                beta = beta_reordered

            # Calculate coherence
            result = calculate_coherence_with_gensim(documents, vocab, beta, k)
            results[f"k{k}"] = result

        except FileNotFoundError as e:
            print(f"  SKIP: {e}")
            continue
        except Exception as e:
            print(f"  ERROR: {e}")
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

    print(f"\nSaved results to {output_path}")

    # Print summary
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)

    # Sort by coherence_cv
    sorted_results = sorted(results.values(), key=lambda x: x["coherence_cv"], reverse=True)

    print("\nCoherence Scores (higher is better):")
    for r in sorted_results:
        print(f"  K={r['k']}: C_v={r['coherence_cv']:.4f}, U_MASS={r['coherence_umass']:.4f}")

    optimal_k = sorted_results[0]["k"]
    print(f"\nOptimal K by C_v coherence: {optimal_k}")

    # Show top words for optimal K
    print(f"\nTop words for K={optimal_k}:")
    for i, words in enumerate(results[f"k{optimal_k}"]["top_words"]):
        print(f"  Topic {i+1}: {', '.join(words[:10])}")

    print("\n" + "="*60)
    print("DONE")
    print("="*60)


if __name__ == "__main__":
    main()
