# -*- coding: utf-8 -*-
"""
Script to process values of chartevents items. Values often contain
numerical values and free text, and semantically meaningful modifications
to the item description itself.
"""

import numpy as np
import pandas as pd
from string import maketrans, digits
import cPickle as pickle


def map_numeric_to_nan(value):
    """Maps symbols to spaces and deletes digits from values."""
    trantab = maketrans('#%^&*!@()-=/.:;,\\', ' ' * 17)
    value = str(value).translate(trantab, digits)
    if value.strip(' ') == '':
        return np.nan
    else:
        return value.translate(trantab, digits).lower()


def map_to_new_id(itemid_value_tuple, index_dict):
    """Map itemid-value combo to a new itemid."""
    if itemid_value_tuple not in index_dict:
        return itemid_value_tuple[0]
    else:
        return itemid_value_tuple[0] + \
            '_' + str(index_dict[itemid_value_tuple])


if __name__ == "__main__":
    # Parse csv
    main_dir = '/tmp/event-cui-transfer/'
    has_str_val = {}
    line_count = 0
    item_descriptions = {}
    all_labels = []
    label = {}
    ind_dict = {}
    trantab = maketrans('#%^&*!@()-=/.:;,\\', ' ' * 17)
    with open(main_dir + '/unique_chart_item_values.csv', 'r') as f:
        for line in f:
            line_count += 1
            if line_count == 1:
                continue
            process_line = line[2:-3]
            elements = process_line.split(',')
            for element in range(len(elements)):
                elements[element] = elements[element].strip('"')
            label[elements[0]] = elements[-2]
            value = elements[-1].translate(trantab, digits)
            print label[elements[0]] + ' ' + value
            # if value is a number, don't care about this line.
            if value.strip(' ') == '':
                continue
            else:
                itemid = elements[0]
                if itemid in has_str_val:
                    has_str_val[itemid].append(value)
                else:
                    has_str_val[itemid] = [value]
    for key in has_str_val:
        has_str_val[key] = [val.lower() for val in has_str_val[key]]
        has_str_val[key] = list(set(has_str_val[key]))
        ind = 0
        for val in has_str_val[key]:
            ind += 1
            itemid = str(key) + '_' + str(ind)
            item_descriptions[itemid] = label[key] + ' ' + val
            ind_dict[(key, val)] = ind

    itemids_with_vals = has_str_val.keys()
    # Dump dictionary to file.
    pickle.dump(ind_dict, open(main_dir + '/chart_item_value_dict.p','w'))
    pickle.dump(itemids_with_vals, open(main_dir + '/itemids_with_vals.p', 'w'))

    # Process chartevents.
    filename = main_dir + '/chartevents_withvalue_0to24hrs.csv'
    chart_events = pd.read_csv(filename, sep=';', header=0)
    chart_events['itemid'] = chart_events['itemid'].astype(str)
    chart_events['value'] = chart_events['value'].astype(str)
    chart_events['value'] = chart_events['value'].apply(map_numeric_to_nan)
#    chart_events = chart_events.dropna(axis=0, subset=['value'])
    chart_events['itemid_value'] = zip(chart_events['itemid'],
                                       chart_events['value'])
    chart_events['itemid_ind'] = \
        chart_events['itemid_value'].apply(map_to_new_id, args=(ind_dict,))
    # Save processed chart events to file.
    chart_events.to_csv(main_dir + '/chartevents_withvalue_processed_0to24hrs.csv',
                        sep=';', index=False)
    X = pd.DataFrame.from_dict(item_descriptions, orient='index')
    X = X.rename(columns={0:'label'})
    X.to_pickle(main_dir + '/chartitem_values.p')
