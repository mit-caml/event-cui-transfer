# -*- coding: utf-8 -*-
"""
Library of functions for transforming data from EHR-specific Item IDs to CUIs,
extracting population of interest, retrieving holdout sets from file, and
computing confidence intervals from bootstrapped samples.
"""

from sklearn.utils import resample
from sklearn.feature_extraction.text import TfidfTransformer
import scipy.sparse
import pandas as pd
import os
from make_filenames import make_filename
from patdata import get_outcome, filter_patients, filter_by_criteria
import numpy as np
from sklearn.metrics import roc_auc_score
import cPickle as pickle
from sklearn import cross_validation


def uniq(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def make_item_CUI_map(itemid_to_CUI_map):
    """Make dictionary mapping each CUI to the itemids that contain it.

    Arguments
    ---------
    itemid_to_CUI_map: dictionary with itemid, list of CUIs
    as key, value pairs.

    Returns
    -------
    CUI_to_itemid_map (dict): CUI (key), corresponding list of itemids (value)

    """

    CUI_to_itemid_map = {}
    for itemid, cuis in itemid_to_CUI_map.items():
        for cui in cuis:
            if cui not in CUI_to_itemid_map:
                CUI_to_itemid_map[cui] = []
            CUI_to_itemid_map[cui].append(itemid)
    CUI_to_itemid_map = {k: uniq(v) for k, v in CUI_to_itemid_map.items()}
    cuis = CUI_to_itemid_map.keys()
    print "Number of unique concepts : ", len(cuis)
    return CUI_to_itemid_map


def map_items_to_CUIs(df, CUI_to_itemid_map):
    """Map bag-of-events DataFrame to bag-of-CUIs DataFrame

    Arguments
    ---------
    df: pandas DataFrame with events data
    CUI_to_itemid_map: dictionary with itemids that contain each CUI.

    Returns
    -------
    new_df: pandas DataFrame with bag-of-CUIs.
    """

    cuis = CUI_to_itemid_map.keys()
    columns = set(df.columns.values)
    new_df = pd.DataFrame()
    for cui in cuis:
        # Find ItemIDs containing each CUI.
        items = list(set(CUI_to_itemid_map[cui]).intersection(columns))
        # Sum counts for items to get count for CUI.
        new_df[cui] = df[items].sum(axis=1)
    columns_keep = new_df.sum(axis=0) > 0
    return new_df[columns_keep[columns_keep == True].index.values]


def load_bow_data(args, time_interval, units, main_dir='/tmp/'):
    """Load BOE data from file.

    Arguments
    ---------
    args: command-line arguments (argparse object)
    time_interval(tuple): start and end to time interval of interest in hours
    units (list): list of care units to load from.
    main_dir (str): main directory

    Returns
    -------
    pandas DataFrame with events data.
    """

    frames = []
    for unit in units:
        # Make filename.
        filename = make_filename(args, unit, time_interval, main_dir)
        # Read data.
        data = pd.read_pickle(filename)
        data.columns = data.columns.astype(str)
        # Rename columns
        rename_dict = {}
        remove_columns = []

        for column in data.columns.values:
            tmp = column.strip('()').split(',')
            tmp = [val.replace('"', '') for val in tmp]
            if tmp[-1] == 'end':
                remove_columns.append(column)
            if tmp[-1] == 'start':
                tmp = ','.join(tmp)
                rename_dict[column] = tmp
        include_columns = list(set(data.columns.tolist()) - set(remove_columns))
        data = data[include_columns]
        data.rename(columns=rename_dict, inplace=True)
        frames.append(data)
    return pd.concat(frames, axis=0).fillna(0)


def extract_population(criteria, patient_info, saps_dict,
                       patients, outcome_str, info_used, gap):
    """
    Extract relevant patient population based on criteria and
    outcome.

    Arguments
    ---------


    Returns
    -------
    """
    patients = filter_by_criteria(criteria, patient_info, patients)
    y = pd.Series(get_outcome(patients, patient_info,
                              outcome_str, info_used, gap),
                  index=patients)
    saps = \
        pd.Series([saps_dict[patient] for patient in patients],
                  index=patients)

    y = y.loc[patients]
    saps = saps.loc[patients]
    return patients, y, saps


def get_holdout_sets(filename, target_pats, y_target):
    """
    Generate holdout sets and save to file, or retrieve from
    file if it exists.

    Arguments
    ---------
    filename: string
    target_pats: list of subject_ids
    y_target: pandas Series, outcome to stratify by.

    Returns
    -------
    subjects_train: list of subject_ids in training set
    subjects_test: list of subject_ids in test set.
    """

    if os.path.exists(filename):
        print "File exists, loading now."
        with open(filename, 'rb') as f:
            subjects_train, subjects_test = pickle.load(f)
        return subjects_train, subjects_test
    else:
        print "File doesn't exist, generating and saving."

        subjects_train, subjects_test = \
            cross_validation.train_test_split(
                target_pats, test_size=0.33, stratify=y_target)
        with open(filename, 'wb') as f:
            pickle.dump((subjects_train, subjects_test), f)
        return subjects_train, subjects_test


def transformTFIDF(X_train_all, X_test_all):
    """Transform bag-of-events using TF-IDF.

    Arguments
    ---------
    X_train_all: pandas DataFrame
    X_test_all: pandas DataFrame

    Returns
    -------
    X_train_t: CSR matrix
    X_test_t: CSR matrix
    """

    tfidf_t = TfidfTransformer(norm='l2',
                               use_idf=True,
                               sublinear_tf=True,
                               smooth_idf=True)
    X_train = scipy.sparse.csr_matrix(X_train_all)
    X_test = scipy.sparse.csr_matrix(X_test_all)
    # Fit TFIDF using training data.
    tfidf_t.fit(X_train)
    # Transform both training and test data.
    X_train_t = tfidf_t.transform(X_train)
    X_test_t = tfidf_t.transform(X_test)
    return X_train_t, X_test_t


def addSAPS(X_train_t, X_test_t, index_train, index_test, saps_dict):
    """Add SAPS-II as a feature.

    Arguments
    ---------
    X_train_t (CSR matrix): TFIDF-transformed BOE features.
    X_test_t (CSR matrix): TFIDF-transformed BOE features.
    index_train (list): subject_ids in training data.
    index_test (list): subject_ids in test data.
    saps_dict (dictionary): contains(subject_id, saps_ii) key, value pairs.

    Returns
    -------
    X_train_sparse: CSR matrix with SAPS-II
    X_test_sparse: CSR matrix with SAPS-II

    """
    train_saps = np.array([saps_dict[subject] for subject in index_train])
    test_saps = np.array([saps_dict[subject] for subject in index_test])

    row_train = np.array([ind for ind in range(len(index_train))])
    row_test = np.array([ind for ind in range(len(index_test))])
    column_train = np.array([0 for ind in range(len(index_train))])
    column_test = np.array([0 for ind in range(len(index_test))])

    train_saps_sparse = scipy.sparse.csr_matrix(
        (train_saps, (row_train, column_train)), shape=(len(index_train), 1))
    test_saps_sparse = scipy.sparse.csr_matrix(
        (test_saps, (row_test, column_test)), shape=(len(index_test), 1))
    X_train_sparse = scipy.sparse.hstack(
        [X_train_t, train_saps_sparse], format='csr')
    X_test_sparse = scipy.sparse.hstack(
        [X_test_t, test_saps_sparse], format='csr')
    return X_train_sparse, X_test_sparse


def get_itemid_CUI_maps(cui_method, main_dir='/tmp/event-cui-transfer/'):
    """Retrieve itemid to CUI mappings from file and create a dictionary
    with the mappings.

    Arguments
    ---------
    main_dir: string
    cui_method: string, one of 'spanning', 'longest', 'all'

    Returns
    -------
    itemid_to_cui_map: dictionary mapping itemid key to list of CUIs
    CUI_to_itemid_map: dictionary mapping each CUI to itemids that contain it.
    """
    assert cui_method in ('spanning', 'longest', 'all')
    itemid_to_cui_map = dict(pickle.load(open(main_dir +
                             'ctakes_extended_' + cui_method + '.p', 'r')))
    CUI_to_itemid_map = make_item_CUI_map(itemid_to_cui_map)
    return itemid_to_cui_map, CUI_to_itemid_map


def process_itemid_keys(itemid_to_cui_map):
    """
    Process itemids by stripping parentheses
    and quotes. Primarily for microbiology event IDs.
    Also filters out items that do not have concept
    mappings.

    Parameters:
    ----------
    itemid_to_cui_map: Dictionary with itemid keys and lists of CUIs as values.

    Returns:
    -------
    new_itemids: list of itemids with at least one corresponding CUI.
    """
    new_itemids = []
    itemids = itemid_to_cui_map.keys()
    for item in itemids:
        if itemid_to_cui_map[item] == []:
            continue
        tmp = item.strip('()').split(',')
        tmp = [val.strip('"') for val in tmp]
        new_itemids.append(','.join(tmp))
    return new_itemids


def filter_data(data,
                itemids,
                filter_threshold,
                outcome_str,
                info_used,
                gap,
                pat_info):
    """Filters data by first filtering patients and then
    filtering events (features) by the number of patients
    they appear in. Items that appear fewer than THRESHOLD
    times are removed.

    Arguments
    ----------
    data (pandas DataFrame)
    new_itemids (list)
    filter_threshold (int)
    outcome_str (string)
    info_used (int)
    gap (int)
    pat_info (pandas DataFrame)

    Returns
    -------
    data_sub (pandas DataFrame): subset of patients and columns
              that are relevant based on filtering criteria.
    """
    patients_include = \
        filter_patients(data.index.values, pat_info,
                        outcome_str, info_used, gap)
    data_filt = data[data.index.isin(patients_include)]
    data_sub = data_filt[
        list(set(itemids).intersection(data_filt.columns.values))]
    # Filter
    restrict = data_sub.apply(lambda column: (
        column != 0).sum()) > filter_threshold
    data_sub = data_sub[restrict.index[restrict == True].values]
    return data_sub


def bootstrap_sample(test_x, test_y, model, n):
    """Stratified bootstrap sampling of test data to
    generate confidence intervals.

    Arguments
    ----------
    test_x (pandas DataFrame): test data features.
    test_y (pandas Series): test outcome.

    Returns
    -------
    CI (tuple): tuple with lower and upper limit of 95% confidence interval
    """
    aucs = []
    for sample in range(n):
        ind_pos = np.where(test_y.values > 0)
        ind_neg = np.where(test_y.values <= 0)
        pos_x = test_x[ind_pos[0], ]
        neg_x = test_x[ind_neg[0], ]
        pos_y = test_y.iloc[ind_pos[0]]
        neg_y = test_y.iloc[ind_neg[0]]
        resampled_pos_x, resampled_pos_y = resample(pos_x, pos_y)
        resampled_neg_x, resampled_neg_y = resample(neg_x, neg_y)
        resampled_x = scipy.sparse.vstack((resampled_pos_x, resampled_neg_x))
        resampled_y = pd.concat((resampled_pos_y, resampled_neg_y), axis=0)
        probs = model.predict_proba(resampled_x)
        aucs.append(roc_auc_score(resampled_y.replace(
            to_replace=-1, value=0), probs[:, 1]))
    # Return 95% confidence interval
    CI = (np.percentile(aucs, 2.5), np.percentile(aucs, 97.5))
    return CI
