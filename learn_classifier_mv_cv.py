# -*- coding: utf-8 -*-
"""
Learn classifier trained on one EHR version and tested on another.
"""

import cPickle as pickle
from make_filenames import initialize_info, make_results_filename
import numpy as np
import pandas as pd
from patdata import get_pat_info
from sklearn.linear_model import LogisticRegression as lr
from sklearn import cross_validation
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.grid_search import GridSearchCV
from sklearn.preprocessing import MaxAbsScaler
from time import time
from utils import *


def main():
    # Initialize.
    args = initialize_info()
    main_dir = args.main_dir
    pat_info = get_pat_info(main_dir)

    db_info = pd.read_csv(
        main_dir + '/patid_dbsource.csv', sep=';', header=0)
    db_dict = dict(zip(db_info.subject_id, db_info.dbsource))
    cv_subjects = []
    mv_subjects = []
    for subject in db_dict:
        if db_dict[subject] == 'carevue':
            cv_subjects.append(subject)
        elif db_dict[subject] == 'metavision':
            mv_subjects.append(subject)
        else:
            print 'ERROR - subject not assigned to db: ', subject
    saps_dict = pat_info['sapsii'].to_dict()

    # Hardcoded parameters.
    units = ['CCU', 'CSRU', 'MICU', 'SICU', 'TSICU']
    info_used = 24 * 60
    outcome_str = args.outcome
    use_saps_vals = [False, True]
    gaps = [hr * 60 for hr in range(0, 60, 12)]
    filter_threshold = args.filter_threshold

    # Initialize dictionaries.
    auc_train = {(info_used, saps, gap): []
                 for gap in gaps for saps in use_saps_vals}
    auc_test = {(info_used, saps, gap): []
                for gap in gaps for saps in use_saps_vals}
    bootstrapped_confidence = {(info_used, saps, gap): []
                               for gap in gaps for saps in use_saps_vals}
    y_test = {(info_used, saps, gap): []
              for gap in gaps for saps in use_saps_vals}
    prob_test = {(info_used, saps, gap): []
                 for gap in gaps for saps in use_saps_vals}
    models = {(info_used, saps, gap): []
              for gap in gaps for saps in use_saps_vals}
    headers = {(info_used, saps, gap): []
               for gap in gaps for saps in use_saps_vals}

    auc_saps = {(info_used, gap): [] for gap in gaps}
    auc_counts = {(info_used, gap): [] for gap in gaps}

    N_train = {(info_used, gap): [] for gap in gaps}
    n_train = {(info_used, gap): [] for gap in gaps}

    N_test = {(info_used, gap): [] for gap in gaps}
    n_test = {(info_used, gap): [] for gap in gaps}
    time_interval = (0, info_used / 60)

    # Model learning pipeline.
    pipeline = Pipeline([('normalize', MaxAbsScaler()),
                         ('clf', lr(penalty=args.penalty,
                                    class_weight='balanced',
                                    solver='liblinear'))])

    # Load all data.
    data_old = {}
    subjects_byunit = {}
    for unit in units:
        print "Loading data for unit ", unit
        t0 = time()
        data_old[unit] = load_bow_data(args, time_interval, [unit], main_dir)
        print "Data loaded. Time elapsed: %3f" % (time() - t0)
        subjects_byunit[unit] = data_old[unit].index.values
    # Concatenate data.
    data_all = pd.concat(data_old.values(), axis=0).fillna(0)
    # print data_all.columns.tolist()
    # Drop data if there are both carevue and metavision itemids.
    if args.drop:
        print "Dropping subjects ... , Number of subjects : ", data_all.shape
        nonmatching_subjects = \
            pd.read_csv(main_dir + 'mv_cv_patient_intersection.csv', sep=';')
        # print nonmatching_subjects.head()
        # print data_all.head()
        subjects_include = list(
            set(data_all.index.tolist()) - set(nonmatching_subjects['subject_id'].tolist()))
        print "Shape before filtering : ", data_all.shape
        data_all = data_all[data_all.index.isin(subjects_include)]
        print "Shape after filtering : ", data_all.shape
    itemid_to_cui_map, CUI_to_itemid_map = \
        get_itemid_CUI_maps(args.cui_method, main_dir)
    # new_itemids = process_itemid_keys(itemid_to_cui_map)
    new_itemids = data_all.columns.tolist()
    # Specify training DB and testing DB.
    if args.traindb == 'metavision':
        subjects_train = mv_subjects
        subjects_test = cv_subjects
    elif args.traindb == 'carevue':
        subjects_train = cv_subjects
        subjects_test = mv_subjects

    for gap in gaps:
        criteria = {}
        print 'Data to filter shape: ', data_all.shape
        data_int = filter_data(
            data_all, new_itemids, filter_threshold,
            outcome_str, info_used, gap, pat_info)
        print 'Data after filtering: ', data_int.shape
        # Map to CUIs with the specified method.

        if args.map_to_CUI:
            data_int = map_items_to_CUIs(data_int, CUI_to_itemid_map)
            print 'Data after transforming: ', data_int.shape
        parameters = {'clf__C': np.logspace(-7, 0, num=8)}

        target_subjects, y_target, target_saps = \
            extract_population(criteria, pat_info, saps_dict,
                               data_int.index.values, outcome_str,
                               info_used, gap)
        y = y_target
        saps = target_saps
        target_data = data_int[data_int.index.isin(target_subjects)]
        print 'Size of data matrix: ', target_data.shape
        print 'Number of examples remaining: ', len(y)
        print 'Number of adverse events remaining: ', np.sum(y == 1)

        y_all = y
        X_all = target_data
        saps_all = saps

        # training/test
        X_train_all = X_all[X_all.index.isin(subjects_train)]
        y_train_all = y_all.loc[X_train_all.index.tolist()]

        X_test_all = X_all[X_all.index.isin(subjects_test)]
        y_test_all = y_all.loc[X_test_all.index.tolist()]
        saps_test_all = saps_all.loc[X_test_all.index.tolist()]

        N_train[(info_used, gap)] = len(y_train_all)
        n_train[(info_used, gap)] = np.sum(y_train_all == 1)

        N_test[(info_used, gap)] = len(y_test_all)
        n_test[(info_used, gap)] = np.sum(y_test_all == 1)

        # Find common features between training and test data.

        # Columns in training data with nonzero values.
        headers_train = X_train_all.apply(
            lambda column: (column != 0).sum()) > 0
        headers_train_filtered = headers_train[
            headers_train == True].index.values
        print "Number of headers in training data: ", len(headers_train_filtered)
        # print headers_train_filtered
        # Columns in test data with nonzero values.
        headers_test = X_test_all.apply(lambda column: (column != 0).sum()) > 0
        headers_test_filtered = headers_test[headers_test == True].index.values
        print "Number of headers in test data: ", len(headers_test_filtered)
        # print headers_test_filtered
        # Intersection.
        headers_intersect = list(
            set(headers_train_filtered).intersection(headers_test_filtered))
        print "Number of headers in intersection : ", len(headers_intersect)
        if args.intersection:
            print 'Length of training : ', X_train_all.shape
            print 'Length of test : ', X_test_all.shape
            X_train_all = X_train_all[headers_intersect]
            X_test_all = X_test_all[headers_intersect]
            print 'Length of intersection : ', len(headers_intersect)
            print 'Length of training after intersection : ', X_train_all.shape
            print 'Length of test after intersection : ', X_test_all.shape

        auc_saps[(info_used, gap)].append(
            roc_auc_score(y_test_all.replace(to_replace=-1, value=0),
                          saps_test_all))

        # Transform BOE using TFIDF.
        index_train, index_test = \
            X_train_all.index.values, X_test_all.index.values
        X_train_t, X_test_t = transformTFIDF(X_train_all, X_test_all)
        column_names = list(X_train_all.columns.values)
        column_names_init = column_names
        print("Number of headers : ", len(column_names))
        for use_saps in [True]:
            if use_saps:
                X_train_sparse, X_test_sparse = addSAPS(
                    X_train_t, X_test_t, index_train, index_test, saps_dict)
                column_names = column_names_init + ['SAPS']
            else:
                X_train_sparse, X_test_sparse = X_train_t, X_test_t
            # Get best parameters using grid search and 5-fold
            # cross-validation.
            cv_stratified = \
                cross_validation.StratifiedKFold(
                    y_train_all, n_folds=5,
                    shuffle=False, random_state=None)
            grid_search = GridSearchCV(pipeline,
                                       parameters,
                                       cv=cv_stratified,
                                       verbose=1,
                                       scoring='roc_auc',
                                       refit=True,
                                       n_jobs=8)
            t0 = time()
            grid_search.fit(X_train_sparse, y_train_all)
            best_parameters = grid_search.best_estimator_.get_params()
            for param_name in sorted(parameters.keys()):
                print "\t%s: %r" % (param_name, best_parameters[param_name])

            probs = grid_search.predict_proba(X_test_sparse)
            probs_series = pd.Series(
                probs[:, 1], index=y_test_all.index.values)
            auc_test[(info_used, use_saps, gap)].append(roc_auc_score(
                y_test_all.replace(to_replace=-1, value=0), probs_series))
            probs_train = grid_search.predict_proba(X_train_sparse)
            probs_train_series = pd.Series(
                probs_train[:, 1], index=y_train_all.index.values)
            auc_train[(info_used, use_saps, gap)].append(
                roc_auc_score(y_train_all.replace(to_replace=-1, value=0),
                              probs_train_series))
            print "AUC test : ", auc_test[(info_used, use_saps, gap)]
            y_test[(info_used, use_saps, gap)].append(y_test_all)
            prob_test[(info_used, use_saps, gap)].append(probs_series)

            models[(info_used, use_saps, gap)].append(grid_search)
            headers[(info_used, use_saps, gap)].append(column_names)

            # Bootstrap holdout set to get CI
            bootstrapped_confidence[(info_used, use_saps, gap)].append(
                bootstrap_sample(X_test_sparse, y_test_all, grid_search, 1000))

    results_filename = make_results_filename(args, info_used, gap, main_dir)
    with open(results_filename, 'wb') as f:
        pickle.dump((auc_test, auc_train, auc_saps, y_test,
                     prob_test, auc_counts, models, N_train,
                     n_train, N_test, n_test, headers,
                     bootstrapped_confidence), f)


if __name__ == "__main__":
    main()
