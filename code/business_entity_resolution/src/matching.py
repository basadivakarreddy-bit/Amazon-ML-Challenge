import pandas as pd
from difflib import SequenceMatcher

from preprocessing import normalize_text


def similarity(text1, text2):
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1, text2).ratio()


def calculate_score(source1_data, candidate_data):
    s1_name, s1_address, s1_country = source1_data
    c_name, c_address, c_country = candidate_data

    name_score = similarity(s1_name, c_name)
    address_score = similarity(s1_address, c_address)
    country_score = 1.0 if (s1_country and c_country and s1_country == c_country) else 0.0

    return 0.60 * name_score + 0.30 * address_score + 0.10 * country_score


def prepare_lookup(df):
    lookup = {}
    for row in df.itertuples(index=False):
        entity_id = str(getattr(row, "entity_id"))
        lookup[entity_id] = (
            normalize_text(getattr(row, "business_name", "")),
            normalize_text(getattr(row, "business_address", "")),
            normalize_text(getattr(row, "country", "")),
        )
    return lookup


def _parse_candidate_ids(candidate_value):
    if candidate_value is None or (isinstance(candidate_value, float) and pd.isna(candidate_value)):
        return []

    if isinstance(candidate_value, str):
        text = candidate_value.strip()
        if not text or text.lower() == "nan":
            return []
        values = text.split(",")
    elif isinstance(candidate_value, (list, tuple, set)):
        values = candidate_value
    else:
        values = [candidate_value]

    cleaned = []
    for item in values:
        if item is None:
            continue
        text = str(item).strip()
        if not text or text.lower() == "nan":
            continue
        cleaned.append(text)
    return cleaned


def find_matches(source1, source2, source3, candidate_pairs, threshold=0.70):
    source1_lookup = prepare_lookup(source1)
    source2_lookup = prepare_lookup(source2)
    source3_lookup = prepare_lookup(source3)

    required_ids = [str(item) for item in source1["entity_id"].tolist()]
    result_map = {entity_id: "" for entity_id in required_ids}

    if hasattr(candidate_pairs, "itertuples"):
        pair_rows = candidate_pairs.itertuples(index=False, name=None)
    else:
        pair_rows = candidate_pairs

    for row in pair_rows:
        if len(row) < 2:
            continue

        source1_id = str(row[0])
        candidate_value = row[1]
        s1_data = source1_lookup.get(source1_id)
        if s1_data is None:
            continue

        scored_matches = []
        for candidate_id in _parse_candidate_ids(candidate_value):
            candidate_id = str(candidate_id)

            if candidate_id.startswith("S2-"):
                candidate_data = source2_lookup.get(candidate_id)
            elif candidate_id.startswith("S3-"):
                candidate_data = source3_lookup.get(candidate_id)
            else:
                continue

            if candidate_data is None:
                continue

            score = calculate_score(s1_data, candidate_data)
            if score >= threshold:
                scored_matches.append((candidate_id, score))

        scored_matches.sort(key=lambda item: item[1], reverse=True)
        result_map[source1_id] = ",".join(item[0] for item in scored_matches)

    rows = [
        {"source1_entity_id": entity_id, "matched_entity_ids": result_map.get(entity_id, "")}
        for entity_id in required_ids
    ]
    frame = pd.DataFrame(rows, columns=["source1_entity_id", "matched_entity_ids"])
    frame["matched_entity_ids"] = frame["matched_entity_ids"].fillna("")
    return frame


if __name__ == "__main__":
    print("matching module loaded successfully.")
