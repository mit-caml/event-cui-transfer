# -*- coding: utf-8 -*-
"""
Parse ctakes_output folder for CUIs.
"""
import cPickle as pickle
import os
from lxml import etree


def get_cui_spans(xml_filename):
    """Extract CUI spans from `xml_filename`.

    A CUI span is a tuple (cui, (span_begin, span_end)).

    Arguments
    ---------
    xml_filename (path): the path to the cTAKES xml output file.

    Returns
    -------
    List of unique CUI spans that appear in `xml_filename`.

    """
    tree = etree.parse(xml_filename)

    # textsem.* contains spans
    textsems = tree.xpath('*[@_ref_ontologyConceptArr]')
    span = lambda e: (int(e.get('begin')), int(e.get('end')))
    ref_to_span = {e.get('_ref_ontologyConceptArr'): span(e) for e in textsems}

    # FSArray links UmlsConcept to textsem.*
    fsarrays = tree.xpath('uima.cas.FSArray')
    id_to_ref = {e.text: fs.get('_id') for fs in fsarrays for e in fs}

    # UmlsConcept contains cuis
    umlsconcepts = tree.xpath('org.apache.ctakes.typesystem.type.refsem.UmlsConcept')
    cui_ids = [(c.get('cui'), c.get('_id')) for c in umlsconcepts]

    # unique cui_spans
    id_to_span = lambda _id: ref_to_span[id_to_ref[_id]]
    cui_spans = [(cui, id_to_span(_id)) for cui, _id in cui_ids]

    seen = set()
    seen_add = seen.add
    # print cui_spans
    return [cs for cs in cui_spans if not (cs in seen or seen_add(cs))]


def get_cuis(xml_filename):
    """Extract CUIs from `xml_filename` using "all" method.

    Arguments
    ---------
    xml_filename (path): the path to the cTAKES xml output file.

    Returns
    -------
    Set of "all" unique CUIs that appear in `xml_filename`.
    """
    cui_spans = get_cui_spans(xml_filename)

    return {cui for cui, span in cui_spans}


span_len = lambda s: s[1] - s[0]
cui_span_len = lambda cs: span_len(cs[1])


def get_cuis_preferred(xml_filename):
    """Extract CUIs from `xml_filename` using "spanning" method.

    Arguments
    ---------
    xml_filename (path): the path to the cTAKES xml output file.

    Returns
    -------
    Set of "spanning" unique CUIs that appear in `xml_filename`.
    """
    cui_spans = get_cui_spans(xml_filename)

    # sort cuis by longest span
    cui_spans.sort(key=cui_span_len, reverse=True)

    # return preferred spans
    seen = set()
    seen_add = seen.add

    covered_l = lambda new, old: (new[0] >= old[0] and new[1] < old[1])
    covered_r = lambda new, old: (new[0] > old[0] and new[1] <= old[1])
    covered = lambda new, old: covered_l(new, old) or covered_r(new, old)

    return {cui for cui, span in cui_spans if not (
        any(covered(span, seen_span) for seen_span in seen)
        or seen_add(span))}


def get_cuis_longest(xml_filename):
    """Extract CUIs from `xml_filename` using "longest" method.

    Arguments
    ---------
    xml_filename (path): the path to the cTAKES xml output file.

    Returns
    -------
    Set of "longest" unique CUIs that appear in `xml_filename`.
    """
    cui_spans = get_cui_spans(xml_filename)

    # sort cuis by longest span
    cui_spans.sort(key=cui_span_len, reverse=True)

    # return longest spans
    if cui_spans:
        max_span_len = cui_span_len(cui_spans[0])

    return {cui for cui, span in cui_spans if span_len(span) == max_span_len}


if __name__ == "__main__":
    main_dir = "/tmp/event-cui-transfer/"
    dir_name = main_dir + '/ctakes_output/'
    item_cuis_nodrop = []
    item_cuis_preferred = []
    item_cuis_longest = []
    n_nodrop = []
    n_preferred = []
    n_longest = []
    prescription_lookup = \
        pickle.load(open(main_dir + "prescription_id_dict.p", "r"))
    item_ids_included = []
    files = [f for f in os.listdir(dir_name)
             if os.path.isfile(dir_name + f) and f[0] != '.']
    for fname in files:
        cuis_nodrop = get_cuis(dir_name + fname)
        cuis_preferred = get_cuis_preferred(dir_name + fname)
        cuis_longest = get_cuis_longest(dir_name + fname)
        n_nodrop.append(len(cuis_nodrop))
        n_preferred.append(len(cuis_preferred))
        n_longest.append(len(cuis_longest))
        f_base = fname[:-4]
        # if directory == 'prescriptions':
        if f_base.startswith('prescription'):
            item_id = int(f_base.split("-")[1])
            f_base = prescription_lookup[int(item_id)]
        else:
            item_ids_included.append(f_base)
        item_cuis_nodrop.append((f_base, list(cuis_nodrop)))
        item_cuis_preferred.append((f_base, list(cuis_preferred)))
        item_cuis_longest.append((f_base, list(cuis_longest)))

    nodrop_dict = dict(item_cuis_nodrop)
    preferred_dict = dict(item_cuis_preferred)
    longest_dict = dict(item_cuis_longest)

    main_dir = "/tmp/event-cui-transfer/"
    with open(main_dir + '/ctakes_extended_all.p', 'w') as f_write:
        pickle.dump(item_cuis_nodrop, f_write)
    with open(main_dir + '/ctakes_extended_spanning.p', 'w') as f_write:
        pickle.dump(item_cuis_preferred, f_write)
    with open(main_dir + '/ctakes_extended_longest.p', 'w') as f_write:
        pickle.dump(item_cuis_longest, f_write)
