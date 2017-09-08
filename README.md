Predicting Clinical Outcomes Across Changing Electronic Health Record Systems
=============================================================================
Presented at KDD 2017 in Halifax, Nova Scotia

August 2017

Jen Gong, Tristan Naumann, Peter Szolovits, and John Guttag

CSAIL, MIT

This repository contains the code for experiments detailed in "Predicting Clinical Outcomes Across Changing Electronic Health Record Systems," presented at KDD 2017 in Halifax, Nova Scotia. We utilized data from [MIMIC III](https://mimic.physionet.org/), v 1.3.

This code repository has three parts.
1) **Cohort and data extraction**: we provide PostgreSQL queries for MIMIC III v 1.3 for the cohort, outcome, and feature extraction in [`get_data`](get_data). We assume that several tables provided with the MIMIC installation (e.g., SAPS-II acuity score) have already been built prior to running our code.
* [`full_script.sh`](full_script.sh): Runs relevant SQL queries in the correct sequence to create materialized views for patient cohort extraction.
  * We extract the first ICU stay of all adult (at least 18 yrs old) patients from MIMIC III v 1.3.
      - [`get_data/create_firsticu_careunit_view.sql`](get_data/create_firsticu_careunit_view.sql): Defines the careunit a patient belongs to based on amount of time the patient was in a particular ICU during the beginnign of their stay and extracts the first ICU admission for each adult patient.
      - [`get_data/define_patient_careunit.sql`](get_data/define_patient_careunit.sql): Defines the careunit a patient belongs to based on amount of time the patient was in a particular ICU during the beginnign of their stay.
      - [`get_data/make_itemid_dictionaries.sql`](make_itemid_dictionaries.sql): Copies dictionaries with item descriptions (d_items and d_labitems) to file, and constructs similar dictionaries for microbiologyevents and services.
      - [`get_data/itemid_pat_dbsource_check.sql`](itemid_pat_dbsource_check.sql): Extracts subjects whose ICU stay coincided with the change from CareVue (EHR 1) to MetaVision (EHR 2). These patients are removed in the experimental analysis.
      - [`get_data/copy_unique_item_value_tuples.sql`](copy_unique_item_value_tuples.sql): Copies unique item, value tuples from chartevents to file.
  * We extract data for the first 24 hours of each patient's ICU stay, but the functions that are provided in [`write_functions.sql`](write_functions.sql) can easily be extended to extract the same data for other periods during the patient stay.
      - [`get_data/write_functions.sql`](write_functions.sql): Defines SQL functions for extracting patient identifier, item identifier, value, and time from ICU admission for specified intervals of time.
      - [`get_data/export_data.sql`](export_data.sql): Export chartevents, labevents, inputevents, outputevents, services data to CSV.
      - [`get_data/process_itemid_values.py`](process_itemid_values.py): Process chartevents Item IDs and values, creating new Item IDs for each unique value containing text that modifies a chart item. This is done because many of the charted items have semantically meaningful values that modify the description of the original item.
  * In addition, [`full_script.sh`](full_script.sh) creates relevant directories for cTakes annotation and writes to file the descriptions that will be used as input for cTakes.
2) **Bag-of-events feature construction**: we provide code that generates the bag-of-events feature representation utilized in the paper. This code contains SQL functions to extract the relevant data from the MIMIC-III data warehouse. Data processing functions for these bag-of-events vectors are also implemented.
* [`build_unigram_boe.py`](make_boe_data/build_unigram_boe.py): Functions to build BOE vectors for each subject ID.
* [`generate_data_pipeline.py`](make_boe_data/generate_data_pipeline.py): Script to build BOE vectors for patients from each careunit  based on events during the first 24 hours of the patient's ICU stay.

3) **MIMIC-III Item ID to UMLS Concept Unique Identifier (CUI) mappings**: we pvrovide code that maps the bag-of-events feature representations extracted from MIMIC-III to the UMLS CUI space. This portion of the code requires the user to have a license with UMLS to access the necessary ontologies.
* see the [README](ctakes_cuis/README.md)

4) **Experiments**: setup/prediction code for the experiments detailed in the paper.
* [`learn_classifier_db.py`](learn_classifier_db.py): Trains and evaluates model on a single database version (experiments on CareVue alone or MetaVision alone) to demonstrate the performance of BOE features against SAPS-II and to compare the different methods of mapping to CUIs against using EHR-specific Item IDs.
* [`learn_classifier_mv_cv.py`](learn_classifier_mv_cv.py): Trains a model on one EHR version (either CareVue or Metavision) and tests on the other (Metavision or CareVue). This is done to evaluate portability of a predictive model learned on one EHR and tested on another, using EHR-specific Item IDs and using a shared semantic feature space ([UMLS](https://www.nlm.nih.gov/research/umls/) Concept Unique Identifiers, or CUIs).
