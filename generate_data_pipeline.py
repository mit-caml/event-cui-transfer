# -*- coding: utf-8 -*-
"""
Generate the data pipeline.
"""

from make_filenames import make_filename, initialize_info
from patdata import get_pat_info, filter_by_criteria
from build_unigram_boe import bow_count
import numpy as np
import pandas as pd


def process_csvs(prefixes, suffix, headers_want, main_dir):
    """Process CSVs with events data to have consistent column names.

    Arguments
    ---------
    prefixes (list of str): prefixes describing type of data
    suffix (str): suffix for filename
    headers_want: list of headers to keep
    main_dir (str): directory where data are stored.

    Returns
    -------
    frames_list: list of pandas DataFrames with events data.
    """

    frames_list = []
    for i in range(len(prefixes)):
        filename = main_dir + prefixes[i] + suffix
        tmp = pd.read_csv(filename, sep=';', header=0)
        if 'itemid_ind' in tmp:
            if 'itemid' in tmp:
                tmp.drop(['itemid'], axis=1, inplace=True)
            tmp['itemid_ind'] = tmp['itemid_ind'].astype(str)
            tmp.rename(columns={'itemid_ind': 'itemid'}, inplace=True)
        if 'min_icuin_to_start' in tmp:
            tmp.rename(
                columns={'min_icuin_to_start': 'min_icuin_to_chart'},
                inplace=True)
        if 'id' in tmp:
            tmp.rename(columns={'id': 'itemid'}, inplace=True)
        frames_list.append(tmp[headers_want])
    return frames_list


def load_csvs(time_interval, main_dir):
    """Load CSVs with events data.

    Arguments
    ---------
    time_interval (tuple of ints): tuple specifying data
                                   start and data end times.
    main_dir (str): directory to load from

    Returns
    -------
    data: pandas DataFrame containing subject_id, min_iucin_to_chart, itemid
    """

    # Drop datetimeevents because of inconsistent times.
    prefixes_withtod = ['chartevents_withvalue_processed',
                        'inputevents_mv', 'inputevents_cv',
                        'outputevents', 'labevents',
                        'microbiologyevents_withtime']
    prefixes_notod = ['prescriptions',
                      'microbiologyevents_notime']
    # Parse time interval to suffix.
    suffix = '_' + str(time_interval[0]) + \
        'to' + str(time_interval[1]) + 'hrs.csv'
    suffix_notod = '_' + str(time_interval[0] / 24) + 'day.csv'

    headers_want_withtod = ['subject_id',
                            'min_icuin_to_chart', 'itemid']
    headers_want_notod = ['subject_id', 'days_from_icuin', 'itemid']
    frames_list = []
    frames_list += process_csvs(prefixes_withtod,
                                suffix, headers_want_withtod,
                                main_dir)
    frames_list += process_csvs(prefixes_notod, suffix_notod,
                                headers_want_notod, main_dir)
    data = pd.concat(frames_list, axis=0)
    # Drop duplicate rows
    data = data.drop_duplicates()
    return data


if __name__ == "__main__":
    # Parse arguments from command line.
    args = initialize_info()
    # Specify time intervals and units
    units = ['CCU', 'CSRU', 'MICU', 'SICU', 'TSICU']
    # Ignore events before admission to ICU
    time_interval = (0, 24)
    # Get patient information
    pat_info = get_pat_info(args.main_dir)
    # Load data.
    data = load_csvs(time_interval, args.main_dir)
    print data.head()
    print "Shape : ", data.shape
    # Remove events where min_icuin_to_chart happens outside time scope of
    # outcome.
    disch_time = \
        data.subject_id.map(pat_info['min_icuin_to_discharge'])
    ind = (~(np.isnan(data.min_icuin_to_chart)) &
            (data.min_icuin_to_chart < disch_time)) | \
          (~(np.isnan(data.days_from_icuin)) &
            (data.days_from_icuin <
                np.floor(disch_time/float(60))))
    filtered_data = data[ind]
    print "Filtered data : ", filtered_data.shape
    # Generate vectors for patients in each ICU careunit and save to file.
    for i in range(len(units)):
        filename = make_filename(args, units[i], time_interval, args.main_dir)
        target_criteria = {'unit': [units[i]]}
        # Filter patients
        target_subjects = filter_by_criteria(
            target_criteria, pat_info, data.subject_id)
        target_data = filtered_data[
            filtered_data.subject_id.isin(target_subjects)]
        target_subjects = list(set(target_data['subject_id']))
        target_subjects.sort()
        X = bow_count(target_data, target_subjects)
        print "Saving."
        X.to_pickle(filename)
        print 'Done with unit : ', units[i]
