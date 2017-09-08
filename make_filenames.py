# -*- coding: utf-8 -*-
"""
Functions to get command line arguments for generating BOE data and
training models and to make filenames to save BOE data and results to.
"""

import argparse
import os


def make_filename(args, unit, time_interval, main_dir='/tmp'):
    """Make filename for BOE data.

    Arguments
    ----------
    args (argparse object): command line arguments
    unit (str): care unit name
    time_interval (tuple): beginning hour of ICU stay and end hour of ICU stay
    main_dir (str): main directory


    Returns
    -------
    filename for boe data, str

    """
    file_dir = main_dir + '/bow_data/'
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    file_parts = []
    file_parts.append(unit)
    file_parts.append('afterICUadm')
    file_parts.append('unigrams')

    file_parts.append(
        str(time_interval[0]) + 'to' + str(time_interval[1]) + 'hrs')
    return file_dir + '_'.join(file_parts) + '.p'


def make_results_filename(args, info_used, gap, main_dir='/tmp/'):
    """Make results filename.

    Arguments
    ----------
    args (argparse object): command line arguments
    info_used (int): amount of information used (minutes)
    gap (int): gap size (minutes)
    main_dir (str): directory to save to.

    Returns
    -------
    filename (str)

    """
    results_dir = main_dir + '/results/'
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    file_parts = ['results_unigrams']
    file_parts.append('threshold')
    file_parts.append(str(args.filter_threshold))
    file_parts.append('gap' + str(gap / 60))
    file_parts.append(args.outcome)
    file_parts.append('traindb')
    file_parts.append(args.traindb)
    if args.testdb:
        file_parts.append('testdb')
        file_parts.append(args.testdb)
    if args.drop:
        file_parts.append('drop_nonmatching')
    if args.map_to_CUI:
        file_parts.append('map_to_CUI')
        file_parts.append(args.cui_method)
    if args.intersection:
        file_parts.append('common_features')
    file_parts.append(str(info_used / 60) + 'hrs')
    file_parts.append(args.penalty)
    return results_dir + '_'.join(file_parts) + '.p'


def initialize_info():
    """Initialize command line arguments for BOE data generation
    and model training."""
    parser = argparse.ArgumentParser(
        description="""Concatenate BOW data for specified
                        time interval and outcome.""")
    parser.add_argument("--drop",
                        help="drop nonmatching patients or not",
                        action="store_true")
    parser.add_argument("--traindb", help="database to train on", type=str)
    parser.add_argument("--testdb", help="database to train on", type=str)
    parser.add_argument("--intersection",
                        help="intersect features of training and test or not",
                        action="store_true")
    parser.add_argument("--outcome", help="outcome to predict",
                        default='inhosp')
    parser.add_argument("--filter_threshold",
                        help="at least n occurrences to keep feature",
                        type=int, default=5)
    parser.add_argument("--map_to_CUI", help="map to CUI", action="store_true")
    parser.add_argument("--cui_method",
                        help="method to map CUIs",
                        type=str, default='all')
    parser.add_argument("--penalty",
                        help="Penalty to use. Options are l1 and l2",
                        type=str, default="l2")
    parser.add_argument("--main_dir",
                        help="main directory",
                        default="/tmp/event-cui-transfer/")
    # Get command line arguments.
    args = parser.parse_args()
    return args
