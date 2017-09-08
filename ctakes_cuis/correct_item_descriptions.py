# -*- coding: utf-8 -*-
"""
Modify ambiguous item descriptions.
"""

import editdistance
import enchant
import numpy as np
import pandas as pd
import re
import string
from sklearn.feature_extraction.text import CountVectorizer
from collections import defaultdict
import cPickle as pickle
from string import maketrans
from bs4 import BeautifulSoup
import urllib2


def preprocess_item_descriptions(item_descs):
    """
    """
    itemid_words = {}
    item_text = {}
    items = item_descs.index.values
    for item in items:
        if not isinstance(item_descs.loc[item].label, str):
            if np.isnan(item_descs.loc[item].label):
                temp_str = 'N/A'
            else:
                temp_str = str(item_descs.loc[item].label)
        else:
            temp_str = item_descs.loc[item].label.lower()
        itemid_words[item] = filter(None, re.split(' |,|;', temp_str))
        item_text[item] = " ".join(itemid_words[item])
    return pd.Series(item_text)


def scrape_wiki_abbrevs(main_dir):
    """Get a list of medical abbreviations from Wikipedia.

    Arguments
    ---------
    main_dir (str): directory to store abbreviations
    """

    abbreviation = ""
    meaning = ""

    letters = string.ascii_uppercase
    with open(main_dir + '/wiki_medical_abbrevs.csv', 'w') as f:
        for letter in letters:
            wiki = \
                "https://en.wikipedia.org/wiki/List_of_medical_abbreviations:_" + letter
            # Needed to prevent 403 error on Wikipedia
            header = {'User-Agent': 'Mozilla/5.0'}
            req = urllib2.Request(wiki,headers=header)
            page = urllib2.urlopen(req)
            soup = BeautifulSoup(page)
            table = soup.find("table", { "class" : "wikitable sortable" })

            for row in table.findAll("tr"):
                cells = row.findAll("td")
                # For each "tr", assign each "td" to a variable.
                if len(cells) == 2:
                    abbreviation = cells[0].find(text=True)
                    meaning = cells[1].findAll(text=True)
                for x in range(len(meaning)):
                    write_to_file = abbreviation + "\n"
                    f.write(write_to_file.encode('utf-8'))


def make_medical_vocab(main_dir, metavision):
    """Build medical vocabulary.

    Arguments
    ---------
    main_dir (str): directory to load from
    metavision ():
    """
    to_space = '%.*@!$^+,:"><&[()];\'_='
    trantab = maketrans('%.*@!$^+,:"><&[()];\'_=', ' ' * len(to_space))
    # Preprocess metavision item descriptions.
    mv_item_text = preprocess_item_descriptions(metavision)
    mv_vocab = clean_text(mv_item_text).str.split()

    dx = open(main_dir + '/DATA/ICD-9-CM-v32-master-descriptions/CMS32_DESC_LONG_DX.txt', 'r')
    dx_all_lines = dx.read().replace('\n', ' ')
    dx_all_lines = dx_all_lines.translate(trantab, '#')
    dx_vocab = set(dx_all_lines.lower().split())

    sg = open(main_dir + '/DATA/ICD-9-CM-v32-master-descriptions/CMS32_DESC_LONG_SG.txt', 'r')
    sg_all_lines = sg.read().replace('\n', ' ')
    sg_all_lines = sg_all_lines.translate(trantab, '#')
    sg_vocab = set(sg_all_lines.lower().split())

    rxnorm = pd.read_csv(main_dir + '/DATA/RxNorm_full_04042016/rrf/RXNCONSO.RRF', sep="|",header=None)
    snomed_ct_1 = pd.read_csv(main_dir + '/DATA/SNOMED_CT/sct1_TextDefinitions_en-US_US1000124_20160301.txt', sep="\t")

    snomed_vocab = pd.concat([snomed_ct_1['FULLYSPECIFIEDNAME'], snomed_ct_1['DEFINITION']], axis=0, ignore_index=True) # maybe should filter stop words here.
    snomed_vocab_txt = clean_text(snomed_vocab)
    rxnorm_names = clean_text(rxnorm[14]).str.split()
    abbrevs = pd.read_csv(main_dir + '/wiki_medical_abbrevs.csv', sep=";", header=None)
    vocab = set()
    mv_vocab.apply(vocab.update)
    snomed_vocab_txt.apply(vocab.update)
    abbrevs.apply(vocab.update)
    rxnorm_names.apply(vocab.update)
    vocab.update(dx_vocab)
    vocab.update(sg_vocab)
    vocab.remove(np.nan)
    for i in range(10):
        if i in vocab:
            vocab.remove(i)
    with open(main_dir + '/metavision_ids_icds_vocab_new.txt', 'w') as f:
        f.write("\n".join(vocab))
    return


def clean_text(text):
    """Expands common abbreviations using a hard-coded dictionary.

    Arguments
    ---------
    text (series): series of text to be cleaned

    Returns
    -------
    cleaned_text: series with cleaned text
    """
    trantab = maketrans('%*@!$^+,:\"><&[()]\';_=', ' ' * 21)
    # Hardcoded dictionary of some common abbreviations.
    hardcoded_dict = \
        {'INV': 'Invasive',
         'Inv': 'Invasive', 'AvDO2': 'avdo2', #'arteriojugular venous difference of oxygen'
         'FiO2': 'fio2', 'CaO2': 'cao2', #'fraction inspired oxygen','arterial oxygen concentration'
         's/p': 'status post', 'S/P': 'status post',
         'D/C': 'discontinue', 'RLQ': 'Right Lower Quadrant of Abdomen',
         'RUQ': 'Right Upper Quadrant of Abdomen',
         'LLQ': 'Left Lower Quadrant of Abdomen',
         'LUQ': 'Left Upper Quadrant of Abdomen',
         'RUE': 'Right Upper Extremity',
         'RLE': 'Right Lower Extremity', 'PO': 'by mouth',
         'po': 'by mouth', 'airleak': 'air leak',
         'mlns': 'ml normal saline solution', 'NS': 'normal saline solution',
         'NSS': 'normal saline solution', 'nss': 'normal saline solution',
         'ns': 'normal saline solution', '02sat': 'oxygen saturation',
         'sat02': 'oxygen saturation', 'satO2': 'oxygen saturation',
         'O2sat': 'oxygen saturation', 'LDH': 'Lactate dehydrogenase enzyme',
         'art': 'arterial', 'ART': 'arterial', 'bp': 'blood pressure',
         'BP': 'Blood Pressure',
         'angio': 'angiography', 'NeoSure': 'neosure', 'NeoCate': 'neocate',
         'PRBCS': 'Packed Red Blood Cells', 'PRBCs': 'Packed Red Blood Cells',
         'PRBC\'S': 'Packed Red Blood Cells',
         'PRBC': 'Packed Red Blood Cells', 'prbc': 'Packed Red Blood Cells',
         'BNP': 'Brain natiuretic Peptide',
         'High PIP': 'High Peak Inspiratory Pressure',
         'PIP': 'Peak Inspiratory Pressure',
         'high pip': 'high peak inspiratory pressure',
         'trach': 'tracheal', 'Trach': 'tracheal',
         'baedp': 'Balloon Aortic End-Diastolic Pressure',
         'baedp': 'balloon aortic end-diastolic pressure',
         'kvo': 'keep vein open',
         'KVO': 'Keep Vein Open', 'PTT': 'Partial Thromboplastin Time',
         'ed': 'emergency department',
         'LR': 'lactated Ringer\'s solution',
         'lr': 'lactated Ringer\'s solution',
         '(L)': '(Left)', '(R)': '(Right)', 'Neg': 'negative',
         'Insp': 'Inspiratory',
         'Insp.': 'Inspiratory', 'LCW': 'Left Cardiac Work',
         'LCWI': 'Left Cardiac Work Index',
         'LVSW': 'Left Ventricular Stroke Work'}
    indx = []
    text_all = []
    acronyms = []
    for row in range(len(text)):
        if text.iloc[row] != '' and isinstance(text.iloc[row], str):
            indx.append(text.index.values[row])
            tmp = text.iloc[row].split(' ')
            for word in tmp:
                if sum(1 for c in word if c.isupper()) == len(word):
                    acronyms.append(word)
            tmp = " ".join(tmp)
            tmp = re.sub(r'\b[a-z]', lambda m: m.group().upper(), tmp)
            text_all.append(tmp)
    text_split = pd.Series(text_all, index=indx)
    cleaned_text = text_split.str.split(" ").apply(translate_words, args=[hardcoded_dict,])
    cleaned_text = cleaned_text.str.join(" ").str.translate(trantab, '#').str.lower()
    return cleaned_text


def translate_words(list_of_words, dictionary):
    """Translate words using a dictionary, back off to word if no match.

    Arguments
    ---------
    list_of_words (List[str]): words
    dictionary (dict): translations

    Returns
    -------
    new_list: list of translations.
    """
    new_list = []
    for word in list_of_words:
        if word in dictionary:
            new_list.append(dictionary[word])
        else:
            new_list.append(word)
    return new_list


def best_match(word, corrected_med_list, corrected_english_list):
    min_dist_med = len(word)
    best_med_word = ''
    min_dist_eng = len(word)
    best_eng_word = ''
    for word_t in corrected_med_list:
        if editdistance.eval(word, word_t) < min_dist_med:
            min_dist_med = editdistance.eval(word, word_t)
            best_med_word = word_t

    for word_t in corrected_english_list:
        if editdistance.eval(word, word_t) < min_dist_eng:
            min_dist_eng = editdistance.eval(word, word_t)
            best_eng_word = word_t
    if min_dist_med <= min_dist_eng:
        return best_med_word
    else:
        return best_eng_word


def load_itemids_with_vals(itemids, main_dir):
    """Helper method for loading dataframe of items in itemids from main_dir.

    Argument
    --------
    itemids: itemids for which to load items
    main_dir: directory to load from

    Returns
    -------
    items: items from the
    """
    itemids_with_vals = pickle.load(open(main_dir + '/itemids_with_vals.p'))
    item_labels = pd.read_pickle(main_dir + '/chartitem_values.p').reset_index()
    items_include = list(set(itemids['itemid'].values) - set(itemids_with_vals))
    items_include = [str(item) for item in items_include]
    orig_itemid = {}
    for item in item_labels['index']:
        sep_string = item.split('_')
        orig_itemid[item] = sep_string[0]
    item_labels['orig_id'] = item_labels['index'].replace(orig_itemid)
    item_labels = item_labels[item_labels.orig_id.isin(items_include)]
    item_labels = item_labels.rename(columns={"index":"itemid"})
    item_labels = item_labels.set_index('itemid')

    itemids = itemids.set_index('itemid')
    itemids.index = itemids.index.astype(str)
    items = itemids['label'].loc[items_include]
    items = pd.concat([items, item_labels['label']], axis=0)
    return items


def consolidate_carevue(carevue):
    """Consolidate itsems from CV.
    """
    cv_item_text = clean_text(carevue['label'])
    cv_vectorizer = CountVectorizer(analyzer = "word")
    cv_bow_data = cv_vectorizer.fit_transform(cv_item_text)
    cv_vocab = cv_vectorizer.get_feature_names()
    cv_counts = cv_bow_data.sum(axis=0)

    # Compute edit distance between each element in vocabulary
    # with "dictionary"
    correct_by_count = []
    corrected = {}
    count = 0
    corrected_words = []
    no_match = []
    d = enchant.request_pwl_dict(
        main_dir + "/metavision_ids_icds_vocab_new.txt")
    d_english = enchant.Dict("en_US")
    for word in cv_vocab:
        word = word.lower()
        count += 1
        if not d.check(word) and not d.check(word.upper()) \
           and not d_english.check(word):
            no_match.append(word)
            suggestions = d.suggest(word)
            if suggestions == []:
                corrected[word] = word
            else:
                corrected[word] = best_match(word, suggestions, [])
                corrected_words.append(word)
        else:
            corrected[word] = word
    # apply map to correct spellings
    cv_item_corrected = \
        cv_item_text.str.split().apply(translate_words, args=(corrected,))
    cv_items_spellcheck = cv_item_corrected.str.join(' ')
    cv_items_df = pd.DataFrame({'itemid': cv_items_spellcheck.index.values,
                                'label': cv_items_spellcheck.values})
    grouped = cv_items_df[['itemid', 'label']].groupby('label')
    grouped_trimmed = {}
    for key in grouped.groups.keys():
        # take the minimum itemid corresponding to this description.
        grouped_trimmed[key] = grouped.get_group(key).itemid.astype(str).min()
    dict_consolidate = {}
    for itemid in cv_items_df.itemid.astype(str):
        dict_consolidate[itemid] = []
    for key in grouped.groups.keys():
        values = grouped.get_group(key)
        min_val = min(values.itemid.astype(str))
        for val in values.itemid.astype(str):
            dict_consolidate[val].append(min_val)
    map_to_unique = set()
    for key in dict_consolidate:
        if min(dict_consolidate[key]) not in map_to_unique:
            map_to_unique.add(min(dict_consolidate[key]))
    cv_items_spellcheck.index = cv_items_spellcheck.index.astype(str)
    # filter cv_items_spellcheck so that there are no redundant items
    cv_items_spellcheck2 = cv_items_spellcheck.loc[map_to_unique]
    return cv_item_text, cv_items_spellcheck, \
        cv_items_spellcheck2, dict_consolidate


def consolidate_metavision(metavision, dict_consolidate):
    """Consolidate items from metavision.
    """
    mv_item_text = metavision['label'].dropna()
    mv_vocab = clean_text(mv_item_text).str.split()
    mv_item_text_sorted = mv_vocab.str.join(' ')
    frequency = defaultdict(int)
    for i in range(len(mv_vocab)):
        text = mv_vocab.iloc[i]
        for token in text:
            frequency[token] += 1

    for itemid in mv_vocab.index.values.astype(str):
        dict_consolidate[itemid] = []

    mv_items_df = \
        pd.DataFrame({'itemid':mv_item_text_sorted.index.values,
                      'label':mv_item_text_sorted.values})
    grouped = mv_items_df[['itemid', 'label']].groupby('label')
    grouped_trimmed = {}
    for key in grouped.groups.keys():
        # take the minimum itemid corresponding to this description.
        grouped_trimmed[key] = grouped.get_group(key).itemid.astype(str).min()
    for key in grouped.groups.keys():
        values = grouped.get_group(key)
        min_val = min(values.itemid.astype(str))
        for val in values.itemid.astype(str):
            dict_consolidate[val].append(min_val)
    map_to_unique = set()
    for key in dict_consolidate:
        if min(dict_consolidate[key]) not in map_to_unique:
            map_to_unique.add(min(dict_consolidate[key]))
    return mv_item_text, mv_item_text_sorted, dict_consolidate

if __name__=="__main__":
    # load items
    main_dir = '/tmp/event-cui-transfer/'
    itemids = pd.read_csv(main_dir + 'itemids.csv', sep=';', header=0)
    prescription_labels = pd.read_csv(main_dir + 'prescription_labels.csv', sep=';')
    prescription_labels['drug_name_clean'] = clean_text(prescription_labels['drug_name'])
    prescription_labels = prescription_labels.replace(np.nan, '', regex=True)

    # Drop itemids that link to microbiologyevents
    itemids = itemids[itemids.linksto != 'microbiologyevents']

    # Separate metavision and carevue itemids.
    metavision = itemids[itemids.dbsource == 'metavision']
    carevue = itemids[itemids.dbsource == 'carevue']
    itemids_with_vals = load_itemids_with_vals(carevue[['itemid', 'label']], main_dir)
    mv_itemids_with_vals = load_itemids_with_vals(metavision[['itemid', 'label']], main_dir)
    itemids_with_vals.rename("label")
    mv_itemids_with_vals.rename("label")

    # Construct dictionary with medical terms.
    scrape_wiki_abbrevs(main_dir)
    make_medical_vocab(main_dir, metavision)

    # Spellcheck CV items and MV items.
    cv_item_text, cv_items_spellcheck, cv_items_spellcheck2, dict_consolidate = \
        consolidate_carevue(pd.DataFrame(itemids_with_vals))
    mv_item_text, mv_item_text_sorted, dict_consolidate = \
        consolidate_metavision(pd.DataFrame(mv_itemids_with_vals), dict_consolidate)

    cv_item_text.index = cv_item_text.index.astype(str)
    mv_item_text_sorted.index = mv_item_text_sorted.index.astype(str)
    mv_item_text.index = mv_item_text.index.astype(str)
    cv_items_spellcheck2.index = cv_items_spellcheck2.index.astype(str)

    # Write to file.
    with open(main_dir + '/item_description_spell_check_corrections.txt', 'w') as f:
        for key in dict_consolidate.keys():
            if key in cv_item_text.index:
                 print 'Original: ', cv_item_text.loc[key], ' Updated : ', cv_items_spellcheck2.loc[min(dict_consolidate[key])]
                 print_string = key + ';' + cv_item_text.loc[key]
                 for item in dict_consolidate[key]:
                     print_string += ';' + cv_items_spellcheck2.loc[item]
                 print_string += '\n'
                 f.write(print_string)
            elif key in mv_item_text.index:
                print 'Original: ', mv_item_text.loc[key], ' Updated : ', mv_item_text_sorted.loc[min(dict_consolidate[key])]
                f.write(str(key) + ';' + mv_item_text_sorted.loc[key] + ';' + mv_item_text_sorted.loc[min(dict_consolidate[key])] + '\n')

    # Add prescriptions processing here.
    with open(main_dir + '/prescription_label_itemids.csv', 'w') as f:
        for index, row in prescription_labels.iterrows():
            itemid = ",".join(row[['drug_name', 'route', 'start']])
            label = ",".join(row[['drug_name_clean', 'route', 'start']])
            f.write(";".join([itemid, label]) + "\n")
