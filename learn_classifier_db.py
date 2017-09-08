# -*- coding: utf-8 -*-
"""
Learn and evaluate classifier on a single EHR version.
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
import sys
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

    # Hardcoded parameters
    units = ['CCU', 'CSRU', 'MICU', 'SICU', 'TSICU']
    info_used = 24 * 60
    outcome_str = args.outcome
    use_saps_vals = [False, True]
    gaps = [0, 720, 1440, 2160, 2880]
    filter_threshold = args.filter_threshold
    # withtod_subset = True
    # notod_subset = True
    # afterICUadm = True

    time_interval = (0, info_used / 60)

    # Initialize dictionaries.
    auc_test = {(unit, info_used, saps, gap): []
                for unit in units + ['all']
                for gap in gaps
                for saps in use_saps_vals}
    auc_train = {(unit, info_used, saps, gap): []
                 for unit in units + ['all']
                 for gap in gaps
                 for saps in use_saps_vals}
    y_test = {(unit, info_used, saps, gap): []
              for unit in ['all']
              for gap in gaps
              for saps in use_saps_vals}
    prob_test = {(unit, info_used, saps, gap): []
                 for unit in ['all']
                 for gap in gaps
                 for saps in use_saps_vals}
    models = {(unit, info_used, saps, gap): []
              for unit in ['all']
              for gap in gaps
              for saps in use_saps_vals}
    headers = {(unit, info_used, saps, gap): []
               for unit in ['all']
               for gap in gaps
               for saps in use_saps_vals}

    auc_saps = {(unit, info_used, gap): []
                for unit in units + ['all'] for gap in gaps}
    auc_counts = {(unit, info_used, gap): []
                  for unit in units + ['all'] for gap in gaps}
    N_target = {(unit, info_used, gap): []
                for unit in units + ['all'] for gap in gaps}
    n_target = {(unit, info_used, gap): []
                for unit in units + ['all'] for gap in gaps}

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
    data_all = pd.concat(data_old.values(), axis=0).fillna(0)
    # Drop data if there are both carevue and metavision itemids.
    if args.drop:
        nonmatching_subjects = \
            pd.read_csv(main_dir + 'mv_cv_patient_intersection.csv', sep=';')
        subjects_include = list(
            set(data_all.index.tolist()) - set(nonmatching_subjects['subject_id'].tolist()))
        data_all = data_all[data_all.index.isin(subjects_include)]

    if args.traindb == 'carevue':
        data_all = data_all[data_all.index.isin(cv_subjects)]
    elif args.traindb == 'metavision':
        data_all = data_all[data_all.index.isin(mv_subjects)]
    else:
        print 'ERROR: database not specified correctly.'
        sys.exit()
    itemid_to_cui_map, CUI_to_itemid_map = \
         get_itemid_CUI_maps(args.cui_method, main_dir)
    # new_itemids = process_itemid_keys(itemid_to_cui_map)
    new_itemids = data_all.columns.tolist()
    holdout_dir = main_dir + 'holdout_sets/'
    if not os.path.exists(holdout_dir):
        os.makedirs(holdout_dir)

    for gap in gaps:
        criteria = {}
        print 'Data to filter shape: ', data_all.shape
        data_int = filter_data(
            data_all, new_itemids, filter_threshold,
            outcome_str, info_used, gap, pat_info)
        print 'Data after filtering: ', data_int.shape
        if args.map_to_CUI:
            data_int = map_items_to_CUIs(data_int, CUI_to_itemid_map)
            print "Data after transforming : ", data_int.shape
        data = {}
        for unit in units:
            data[unit] = data_int[data_int.index.isin(subjects_byunit[unit])]
        y = {}
        saps = {}
        target_data = {}
        parameters = {'clf__C': np.logspace(-7, 0, num=8)}
        for unit_ind in range(len(units)):
            target_criteria = {'unit': [units[unit_ind]]}
            target_subjects, y_target, target_saps = \
                extract_population(target_criteria, pat_info, saps_dict,
                                   data[units[unit_ind]].index.values,
                                   outcome_str, info_used, gap)

            target_data[units[unit_ind]] = data[units[unit_ind]][
                data[units[unit_ind]].index.isin(target_subjects)]
            y[units[unit_ind]] = y_target
            saps[units[unit_ind]] = target_saps

            N_target[(units[unit_ind], info_used, gap)] = len(y[units[unit_ind]])
            n_target[(units[unit_ind], info_used, gap)] = np.sum(y[units[unit_ind]] == 1)

        for i in range(10):
            t1 = time()
            subjects_train = []
            subjects_test = []
            subjects_test_byunit = {}
            for unit_ind in range(len(units)):
                filename = \
                    holdout_dir + \
                    args.traindb + '_' + units[unit_ind] + \
                    '_' + outcome_str + '_holdout_iter' + \
                    str(i) + '_allacuity.p'
                subjects_train_tmp, subjects_test_tmp = \
                    get_holdout_sets(filename,
                                     target_data[units[unit_ind]].index.values,
                                     y[units[unit_ind]])
                subjects_train = np.concatenate(
                    [subjects_train, subjects_train_tmp])
                subjects_test = np.concatenate(
                    [subjects_test, subjects_test_tmp])
                subjects_test_byunit[units[unit_ind]] = subjects_test_tmp

            y_all = pd.concat(y.values(), axis=0)
            X_all = pd.concat(target_data.values(), axis=0).fillna(0)

            # Training/test
            # X_train_all = X_all.loc[subjects_train]
            # X_test_all = X_all.loc[subjects_test]
            # y_train_all = y_all.loc[subjects_train]
            # y_test_all = y_all.loc[subjects_test]
            X_train_all = X_all[X_all.index.isin(subjects_train)]
            y_train_all = y_all[y_all.index.isin(subjects_train)]

            X_test_all = X_all[X_all.index.isin(subjects_test)]
            y_test_all = y_all[y_all.index.isin(subjects_test)]

            # Transform BOE using TFIDF.
            index_train, index_test = \
                X_train_all.index.tolist(), X_test_all.index.tolist()
            y_train_all = y_train_all.loc[index_train]
            y_test_all = y_test_all.loc[index_test]
            X_train_t, X_test_t = transformTFIDF(X_train_all, X_test_all)
            column_names = X_train_all.columns.tolist()
            column_names_init = column_names
            for use_saps in [False, True]:
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
                probs = grid_search.predict_proba(X_test_sparse)
                probs_series = pd.Series(
                    probs[:, 1], index=y_test_all.index.values)
                auc_test[('all', info_used, use_saps, gap)].append(
                    roc_auc_score(y_test_all.replace(to_replace=-1, value=0),
                                  probs_series))

                probs_train = grid_search.predict_proba(X_train_sparse)
                probs_train_series = pd.Series(
                    probs_train[:, 1], index=y_train_all.index.values)
                auc_train[('all', info_used, use_saps, gap)].append(
                    roc_auc_score(y_train_all.replace(to_replace=-1, value=0),
                                  probs_train_series))

                y_test[('all', info_used, use_saps, gap)].append(y_test_all)
                prob_test[('all', info_used, use_saps, gap)
                          ].append(probs_series)
                print "AUC test : ", auc_test[('all', info_used, use_saps, gap)]
                print "AUC train : ", auc_train[('all', info_used, use_saps, gap)]
                for unit in units:
                    p_ = probs_series[probs_series.index.isin(
                        subjects_test_byunit[unit])]
                    y_ = y_test_all[y_test_all.index.isin(
                        subjects_test_byunit[unit])].replace(
                            to_replace=-1, value=0)
                    auc_test[(unit, info_used, use_saps, gap)
                             ].append(roc_auc_score(y_, p_))

                models[('all', info_used, use_saps, gap)].append(grid_search)
                headers[('all', info_used, use_saps, gap)].append(column_names)
            print "Time elapsed for one repeat : %3f" % (time() - t1)

    results_filename = \
        make_results_filename(args, info_used, gap, main_dir)
    with open(results_filename, 'wb') as f:
        pickle.dump(
            (auc_test, auc_train, auc_saps,
             y_test, prob_test, auc_counts, models,
             n_target, N_target, headers), f)


if __name__ == "__main__":
    main()
