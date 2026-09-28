import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from matching import find_matches


def test_find_matches_returns_expected_columns():
    source1 = pd.DataFrame({
        'entity_id': ['S1-1', 'S1-2'],
        'business_name': ['Acme Foods', 'Beta Shop'],
        'business_address': ['10 Main St', '2 Side Rd'],
        'country': ['USA', 'USA'],
    })

    source2 = pd.DataFrame({
        'entity_id': ['S2-1', 'S2-2'],
        'business_name': ['Acme Food', 'Gamma Co'],
        'business_address': ['10 Main Street', '4 Other Ave'],
        'country': ['USA', 'USA'],
    })

    source3 = pd.DataFrame({
        'entity_id': ['S3-1'],
        'business_name': ['Beta Foods'],
        'business_address': ['5 Side Rd'],
        'country': ['USA'],
    })

    candidate_pairs = pd.DataFrame({
        'source1_entity_id': ['S1-1', 'S1-2'],
        'candidate_entity_ids': ['S2-1,S3-1', float('nan')],
    })

    result = find_matches(source1, source2, source3, candidate_pairs, threshold=0.70)

    assert list(result.columns) == ['source1_entity_id', 'matched_entity_ids']
    assert result.iloc[0]['source1_entity_id'] == 'S1-1'
    assert 'S2-1' in result.iloc[0]['matched_entity_ids']
    assert result.iloc[1]['matched_entity_ids'] == ''
