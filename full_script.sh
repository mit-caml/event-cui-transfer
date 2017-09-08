#!/usr/bin/env bash

# Create temporary folder for intermediate files
mkdir -p /tmp/event-cui-transfer

# Create materialized view defining patient careunit and extracting first ICU stays.
psql mimic -f get_data/create_firsticu_careunit_view.sql
# Define patient careunit.
psql mimic -f get_data/define_patient_careunit.sql
# Get patient database source.
psql mimic -f get_data/patid_dbsource.sql
# Make item ID dictionaries for different tables.
psql mimic -f get_data/make_itemid_dictionaries.sql
# Get CSV with itemid and patient dbsources.
psql mimic -f get_data/itemid_pat_dbsource_check.sql
# Copy chartevents itemids and values to file.
psql mimic -f get_data/unique_chart_item_value_tuples.sql
# Define prescriptions_generic view
psql mimic -f get_data/prescriptions_generic.sql
# Define functions for extracting BOE
psql mimic -f get_data/write_functions.sql

# Export BOE data.
psql mimic -f get_data/export_data.sql

# Modify chartevent values; create new item IDs for items with text values.
python get_data/process_itemid_values.py

# Stage for cTAKES annotation
mkdir -p /tmp/event-cui-transfer/ctakes_input
mkdir -p /tmp/event-cui-transfer/ctakes_output

# Download additonal data resources
mkdir -p /tmp/event-cui-transfer/DATA
cd /tmp/event-cui-transfer/DATA
wget https://www.cms.gov/Medicare/Coding/ICD9ProviderDiagnosticCodes/Downloads/ICD-9-CM-v32-master-descriptions.zip
unzip -d ICD-9-CM-v32-master-descriptions ICD-9-CM-v32-master-descriptions.zip
cd -

# Remind the user that they need to download additional data
echo "Download RxNorm_full_04042016.zip and unzip into /tmp/event-cui-transfer/DATA."
echo "  See: https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormarchive.html"
echo "Download SNOMED_CT and unzip into /tmp/event-cui-transfer/DATA."
echo "  See: https://www.nlm.nih.gov/healthit/snomedct/us_edition.html"

python ctakes_cuis/correct_item_descriptions.py
python ctakes_cuis/write_to_folder.py

# Run cTAKES -- NOTE, ctakes installation script (ctakes_cuis/install_ctakes.sh)
# MUST be run before this.
cd /tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/
./bin/ctakes_cli.sh cas_processer.xml
cd - # Go back to previous directory.

# Get cTAKES annotations
python ctakes_cuis/get_ctakes_cuis_from_items.py

# Generate BOW data.
python generate_data_pipeline.py

# Learn models.
./learn_models.sh
