mkdir -p /tmp/event-cui-transfer/ctakes
cd /tmp/event-cui-transfer/ctakes

# 1. Download cTAKES and resources
wget http://download.nextag.com/apache//ctakes/ctakes-3.2.2/apache-ctakes-3.2.2-bin.tar.gz
wget https://sourceforge.net/projects/ctakesresources/files/ctakes-resources-3.2.0.zip

# 2. Install cTAKES
tar -xvf apache-ctakes-3.2.2-bin.tar.gz
echo "ctakes-resources-3.2.2 requires sudo access during unzip, please enter your password."
sudo unzip ctakes-resources-3.2.0.zip
cp -R resources/* apache-ctakes-3.2.2/resources
#ditto resources/* apache-ctakes-3.2.2/resources

cd -

# 3. Copy the files for headless processing
cp ExtendedUMLSProcessor.xml /tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/desc/ctakes-clinical-pipeline/desc/analysis_engine/
cp cas_processor.xml /tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/
cp ctakes_cli.sh /tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/bin/
mv /tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/resources/org/apache/ctakes/dictionary/lookup/LookupDesc_Db.xml /tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/resources/org/apache/ctakes/dictionary/lookup/LookupDesc_Db.xml.bkp
cp LookupDesc_Db.xml /tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/resources/org/apache/ctakes/dictionary/lookup/

# Remind the user that they need to specify umlsuser and umlspw
echo "Please specify ctakes.umlsuser and ctakes.umlspw in:"
echo "  /tmp/event-cui-transfer/ctakes/apache-ctakes-3.2.2/bin/ctakes_cli.sh"
