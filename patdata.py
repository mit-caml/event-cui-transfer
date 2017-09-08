# -*- coding: utf-8 -*-
"""
Functions to retrieve patient information and filter based on user-specified
criteria, as well as time of death and time of discharge.
"""

import pandas as pd
import numpy as np


def get_pat_info(main_dir='/tmp/'):
    """Get patient information, including DOD, SAPS-II, corresponding to
    subject_id.

    Arguments
    ----------
    main_dir (str): directory to load files from. /tmp/ by default.

    Returns
    -------
    pat_info (pandas DataFrame): Contains date of death, SAPS-II score, etc.
                                 indexed by subject_id.
    """
    pat_info = pd.read_csv(main_dir + '/patid_dod_saps.csv', sep=';', header=0)
    pat_info.set_index(['subject_id'], inplace=True)
    return pat_info


def filter_by_criteria(criteria, pat_info, unique_subjects):
    """Filters data based on target criteria. Returns list of
    subject_ids that satisfy the criteria.

    target_criteria should just be name of careunit of interest.
    Currently only supports key of "unit." Other criteria can easily
    be added to the dictionary, with additional if statements to define
    appropriate behavior.

    Arguments
    ---------
    criteria (dict): criteria to filter by.
    pat_info (pandas DataFrame): patient information
    unique_subjects (list): list of unique subjects in data

    Returns
    -------
    target_subjects (set): set of subjects to keep.
    """

    ind = pd.Series([True] * len(pat_info.index.values),
                    index=pat_info.index.values)
    for key in criteria.keys():
        if key == 'unit':
            # match string. Find subjects where curr_careunit is the right
            # value.
            tmp = (pat_info.curr_careunit.isin(criteria['unit']))
        ind = ind & tmp

    target_subjects = set(pat_info[ind].index.values).intersection(
        set(unique_subjects))
    return target_subjects


def filter_patients(subject_ids, pat_info, outcome_str, info_used, gap):
    """Filter patients based on information of time of discharge and death.
    Patients who are discharged or die before info_used + gap hours of stay
    are removed.

    Arguments
    ---------
    subject_ids (list): initial subject ids.
    pat_info (pandas DataFrame): patient information
    outcome_str (string): outcome wanted
    info_used (int): amount of information used (minutes)
    gap (int): prediction gap to use (minutes)

    Returns
    -------
    filtered_subjects (set): subjects to keep

    """
    icuin_to_dod_dict = pat_info['min_icuin_to_dod'].to_dict()
    icuin_to_discharge_dict = pat_info['min_icuin_to_discharge'].to_dict()
    LOS_cutoff = np.percentile(icuin_to_discharge_dict.values(), 75)
    print 'LOS cutoff , filtering : ', LOS_cutoff / float(60 * 24)

    # Make dataframe with this information.
    time_info = pd.DataFrame({'icuin_to_dod': icuin_to_dod_dict,
                              'icuin_to_discharge': icuin_to_discharge_dict})
    list_to_drop = \
        (~(np.isnan(time_info['icuin_to_dod'])) &
          (time_info['icuin_to_dod'] <= (info_used + gap))) | \
        ((outcome_str == 'inhosp') &
         (time_info['icuin_to_discharge'] <= (info_used + gap))) | \
        ((outcome_str == 'prolonged_los') &
            ((time_info['icuin_to_discharge'] <= (info_used + gap)) |
                (time_info['icuin_to_dod'] <= LOS_cutoff)))
    # Include patient only if patient has not experienced outcome or
    # been discharged during interval of info_used + gap.
    print 'Number of patients initially : ', len(subject_ids)
    keep = list_to_drop[list_to_drop == False].index.tolist()
    filtered_subjects = set(keep).intersection(subject_ids)
    print 'Number of patients left : ', len(filtered_subjects)
    return filtered_subjects


def get_outcome(subject_ids, pat_info, outcome_str, info_used, gap):
    """Get outcome corresponding to outcome_str of subject_ids of interest.

    Arguments
    ---------
    subject_ids (list of ints): subject ids of interest
    pat_info (pandas DataFrame): patient information, including time to death,
        discharge, etc.
    outcome_str (str): outcome of interest
    info_used (int): amount of information used (minutes)
    gap (int): prediction gap (minutes)


    Returns
    -------
    y (list): outcomes corresponding to subject_ids.

    """
    # died during stay in the unit or within 24 hours from being transferred
    # out/discharged.
    icuin_to_dod_dict = pat_info['min_icuin_to_dod'].to_dict()
    icuin_to_discharge_dict = pat_info['min_icuin_to_discharge'].to_dict()
    y = []
    if outcome_str == 'inhosp':
        # in-hospital mortality (pre-discharge)
        for subject_id in subject_ids:
            if not (np.isnan(icuin_to_dod_dict[subject_id])) \
                    and (icuin_to_dod_dict[subject_id] <=
                         icuin_to_discharge_dict[subject_id]):
                y.append(1)
            else:
                y.append(-1)
    elif outcome_str == 'prolonged_los':
        LOS_cutoff = np.percentile(icuin_to_discharge_dict.values(), 75)
        print 'LOS cutoff , getting outcome : ', LOS_cutoff / float(60 * 24)

        print LOS_cutoff
        for subject_id in subject_ids:
            if icuin_to_discharge_dict[subject_id] > LOS_cutoff:
                y.append(1)
            else:
                y.append(-1)
    return y
