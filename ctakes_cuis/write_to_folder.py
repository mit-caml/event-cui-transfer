# -*- coding: utf-8 -*-
"""
Write itemids to ctakes_input folder for processing.
"""
import cPickle as pickle
from string import maketrans


def main(main_dir="/tmp/event-cui-transfer/"):
    tran_chars = '#%^&*!@()[]=.:;\\+\'\"'
    trantab = maketrans(tran_chars, ' ' * len(tran_chars))

    # Get microbiology (item, description) tuples
    with open(main_dir + 'microbiologyevents_itemids.csv', 'r') as f:
        microbiologyevents = f.readlines()

    n_rows = 0
    microbio_itemids = []
    for idx, row in enumerate(microbiologyevents):
        if idx == 0:
            continue
        row = row.strip("\n").split(";")
        itemid = row[0]
        microbio_itemids.append(itemid)
        description = row[1]
        description = description.translate(trantab, '')

        out_path = main_dir + "/ctakes_input/{}".format(itemid)
        with open(out_path, 'w') as f:
            f.write(description)
        n_rows += 1

    with open(main_dir + "/prescription_label_itemids.csv") as f:
        prescription_descriptions = f.readlines()

    prescription_id_dict = {}
    for idx, row in enumerate(prescription_descriptions):
        if idx == 0:
            continue
        row = row.strip("\n").split(";")
        prescription_id_dict[idx] = row[0]
        out_path = main_dir + "/ctakes_input/prescription-{}".format(idx)
        with open(out_path, 'w') as f:
            f.write(row[1])
    pickle.dump(prescription_id_dict, open(main_dir + 'prescription_id_dict.p', 'w'))

    with open(main_dir + 'item_description_spell_check_corrections.txt', 'r') as f:
        chart = f.readlines()
    with open(main_dir + 'lab.csv', 'r') as f:
        lab = f.readlines()

    # Chart.
    n_rows = 0
    for idx, row in enumerate(chart):
        row = row.strip("\n")
        row = row.split(";")
        itemid = row[0]
        description = row[1]
        description_spellcheck = row[2]
        out_path = main_dir + "/ctakes_input/{}".format(itemid)
        with open(out_path, 'w') as f:
            f.write("{}\n{}".format(description.translate(trantab, ''),
                    description_spellcheck))
        n_rows += 1
    print n_rows

    # Lab.
    n_rows = 0
    for idx, row in enumerate(lab):
        if idx == 0:
            continue
        row = row.strip("\n").split(";")
        itemid = row[0]
        description = row[1]
        fluid = row[2]
        category = row[3]
        out_path = main_dir + "/ctakes_input/{}".format(itemid)
        description_str = " ".join([description, fluid, category]).translate(trantab, '')
        with open(out_path, 'w') as f:
            f.write(description_str)
        n_rows += 1
    print n_rows

if __name__ == '__main__':
    main()
