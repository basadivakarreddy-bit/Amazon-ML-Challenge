import argparse
import os
import sys


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
DEFAULT_DATASET_DIR = os.path.join(PROJECT_DIR, "data")
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate blocking candidates and run the entity matching pipeline for Source 1/2/3."
    )
    parser.add_argument("--dataset-dir", default=DEFAULT_DATASET_DIR, help="Directory containing test_source1.tsv, test_source2.tsv, and test_source3.tsv.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory where candidate_pairs.tsv and matching_results.tsv are written.")
    parser.add_argument("--max-candidates", type=int, default=100, help="Max candidate IDs retained per Source-1 entity.")
    parser.add_argument("--threshold", type=float, default=0.70, help="Similarity threshold used for final matching.")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    source1_path = os.path.join(args.dataset_dir, "test_source1.tsv")
    source2_path = os.path.join(args.dataset_dir, "test_source2.tsv")
    source3_path = os.path.join(args.dataset_dir, "test_source3.tsv")

    for path in [source1_path, source2_path, source3_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing required dataset file: {path}")

    sys.path.insert(0, CURRENT_DIR)

    from preprocessing import load_source
    from blocking import generate_candidate_pairs, generate_candidate_pairs_for_matching
    from matching import find_matches

    source1 = load_source(source1_path)
    source2 = load_source(source2_path)
    source3 = load_source(source3_path)

    print("\nLoading test data...")
    print(f"Source 1 rows: {len(source1)}")
    print(f"Source 2 rows: {len(source2)}")
    print(f"Source 3 rows: {len(source3)}")

    print("\nGenerating candidate pairs...")
    candidate_path = os.path.join(args.output_dir, "candidate_pairs.tsv")
    generate_candidate_pairs(source1, source2, source3, output_path=candidate_path, max_candidates=args.max_candidates)
    candidate_pairs = generate_candidate_pairs_for_matching(source1, source2, source3, max_candidates=args.max_candidates)

    print(f"Candidate rows: {len(candidate_pairs)}")
    print(f"\nCandidate file created:\n{candidate_path}")

    print("\nRunning entity matching...")
    matching_results = find_matches(source1, source2, source3, candidate_pairs, threshold=args.threshold)

    required_ids = [str(item) for item in source1["entity_id"].tolist()]
    matching_results = matching_results.set_index("source1_entity_id").reindex(required_ids).fillna("").reset_index()

    matching_path = os.path.join(args.output_dir, "matching_results.tsv")
    matching_results.to_csv(matching_path, sep="\t", index=False, encoding="utf-8")
    print(f"\nMatching results written to:\n{matching_path}")

    non_empty = matching_results["matched_entity_ids"].astype(str).str.strip().ne("").sum()
    print(f"\nMatching file created:\n{matching_path}")
    print(f"\nTotal Source-1 entities: {len(matching_results)}")
    print(f"Entities with at least one match: {non_empty}")
    print(f"Entities with no match: {len(matching_results) - non_empty}")
    print("\nPIPELINE COMPLETED.")


if __name__ == "__main__":
    main()