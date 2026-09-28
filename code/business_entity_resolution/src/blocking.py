import csv
import pandas as pd


def prepare_dataframe(df):
    """
    Create compact blocking keys.
    """

    df = df.copy()

    name = (
        df["business_name_normalized"]
        .fillna("")
        .astype(str)
    )

    address = (
        df["business_address_normalized"]
        .fillna("")
        .astype(str)
    )

    country = (
        df["country_normalized"]
        .fillna("")
        .astype(str)
    )

    df["name_key"] = country + "|" + name.str[:6]
    df["address_key"] = country + "|" + address.str[:8]

    return df


def build_lookup(df):
    """Build lookup: blocking key -> entity IDs."""
    lookup = {}
    for key, group in df.groupby("name_key"):
        lookup[key] = group["entity_id"].tolist()
    return lookup


def build_address_lookup(df):
    """Build address blocking lookup."""
    lookup = {}
    for key, group in df.groupby("address_key"):
        lookup[key] = group["entity_id"].tolist()
    return lookup


def generate_candidate_pairs_for_matching(source1_df, source2_df, source3_df, max_candidates=100):
    """Return a DataFrame with source1_entity_id and candidate_entity_ids."""
    s1 = prepare_dataframe(source1_df)
    s2 = prepare_dataframe(source2_df)
    s3 = prepare_dataframe(source3_df)

    s2_name_lookup = build_lookup(s2)
    s2_address_lookup = build_address_lookup(s2)
    s3_name_lookup = build_lookup(s3)
    s3_address_lookup = build_address_lookup(s3)

    rows = []
    for row in s1.itertuples(index=False):
        candidates = []
        candidates.extend(s2_name_lookup.get(row.name_key, []))
        candidates.extend(s3_name_lookup.get(row.name_key, []))
        candidates.extend(s2_address_lookup.get(row.address_key, []))
        candidates.extend(s3_address_lookup.get(row.address_key, []))
        candidates = list(dict.fromkeys(candidates))[:max_candidates]
        rows.append((str(row.entity_id), ",".join(map(str, candidates))))

    return pd.DataFrame(rows, columns=["source1_entity_id", "candidate_entity_ids"])


def generate_candidate_pairs(source1_df, source2_df, source3_df, output_path=None, max_candidates=100):
    """
    Generate a manageable candidate_pairs.tsv and optionally write it to disk.
    Candidates are obtained from strong business-name and address blocks,
    with at most max_candidates retained per Source-1 entity.
    """
    print("Preparing blocking keys...")
    candidate_frame = generate_candidate_pairs_for_matching(source1_df, source2_df, source3_df, max_candidates=max_candidates)
    total = len(candidate_frame)

    if output_path is not None:
        with open(output_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow(["source1_entity_id", "candidate_entity_ids"])
            for _, row in candidate_frame.iterrows():
                writer.writerow([row["source1_entity_id"], row["candidate_entity_ids"]])

        print("Candidate generation completed.")
        print(f"Rows written: {total:,}")
        print(f"Maximum candidates per S1: {max_candidates}")
        print(f"Output: {output_path}")

    return candidate_frame


if __name__ == "__main__":
    print("Optimized blocking module loaded.")