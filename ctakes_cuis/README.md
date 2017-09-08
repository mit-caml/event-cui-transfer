Installing cTAKES
================

This work uses [Apache TAKES](http://ctakes.apache.org/) version 3.2.2. Instructions for the installation of this version are provided by Apache: https://cwiki.apache.org/confluence/display/CTAKES/cTAKES+3.2+User+Install+Guide. For convenience, we have also provided `install_ctakes.sh` which will download and install cTAKES to `/tmp/event-cui-transfer/ctakes/`.

## 1. Download cTAKES and resources

Per the instruction guide, download cTAKES and the corresponding resource files. This work uses `apache-ctakes-3.2.2-bin` and `ctakes-resources-3.2.0`. The use of these resources requires adding UMLS access rights as described in the "Recommended" section at the end of the installation guide.

## 2. Install cTAKES

Rather than install to the default path, we recommend installing cTAKES to `/tmp/event-cui-transfer/ctakes/`. This is particularly important if you have an alternate version of cTAKES already installed on the system.

## 3. Copy the files for headless processing

Copy the following files (required for headless processing) into the cTAKES installation:

- `ExtendedUMLSProcessor.xml`: Copy to `/tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/desc/ctakes-clinical-pipeline/desc/analysis_engine/`.
- `cas_processor.xml`: Copy to `/tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/`.
- `ctakes_cli.sh`: Copy to `/tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/bin/`.
- `LookupDesc_Db.xml`: Copy to `/tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/resources/org/apache/ctakes/dictionary/lookup/`.


Running cTAKES
================
Run cTAKES using either the CPE or the headless (i.e. command line) usage installed above. 

For the CPE (i.e. `runctakesCPE.sh`), specify the following:

- In Menu, select File > Open CPE Descriptor.
- Navigate to `ExtendedUMLSProcessor.xml`.
- Change the Collection Reader input directory to the `ctakes_input` path.
- Change the output directory to the `ctakes_output` path.

For the command line, run `bin/ctakes_cli.sh cas_processor.xml` from `/tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/`.


Parse cTAKES output
================
Run `get_ctakes_cuis_from_items.py` to extract CUIs from the cTAKES output.