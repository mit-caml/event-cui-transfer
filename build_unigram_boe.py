# -*- coding: utf-8 -*-
"""
Functions to build unigram boe features.
"""

import pandas as pd
from time import time


def make_unigram_features(df, subject_id):
    """Make unigram feature vectors for each subject's care events.

    Arguments
    ---------
    df: pandas DataFrame
    subject_id: integer

    Returns
    -------
    Dictionary containing (itemid, count) key,value pairs.
    Empty dictionary if no events.

    """
    if hasattr(df.ix[subject_id]['itemid'], '__iter__'):
        return dict(zip(df.ix[subject_id]['itemid'],
                        df.ix[subject_id]['count']))
    else:
        return {}


def bow_count(data, unique_subjects):
    """Generates unigrams representation for each subject.

    Arguments
    ---------
    data: pandas DataFrame with data generated
          in MIMIC-III 1v3 PostgreSQL database
          using functions in write_functions.sql.

    unique_subjects: list of subject_ids.

    Returns
    -------
    X : pandas sparse DataFrame with subject IDs as index,
        Item IDs as columns, counts as values.

    """
    counts_dict = {}
    print 'Starting to build BOW dictionaries for patients ...'
    counts = \
        data.groupby(
            ['subject_id', 'itemid']).size()
    counts = counts.reset_index(name="count").set_index(['subject_id'])
    t0 = time()
    for i in range(len(unique_subjects)):
        unigrams = {}
        print 'Subject number : %d' % i
        print 'elapsed time : %3fs' % (time() - t0)
        t0 = time()
        unigrams = make_unigram_features(counts, unique_subjects[i])
        if bool(unigrams):
            counts_dict[unique_subjects[i]] = unigrams
    X = pd.DataFrame.from_dict(counts_dict, orient='index')
    print 'Done building BOW dictionaries for patients ...'
    return X.to_sparse(fill_value=0)
