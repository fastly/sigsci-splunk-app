#!/bin/sh

APPFOLDER="sigsci_TA_for_splunk"
BASEDIR=$PWD
SPLUNKDIR=/opt/splunk
SPLUNKAPP=$SPLUNKDIR/etc/apps
MYUSER=`whoami`

#Clean up files from previous run
sudo rm -rf $BASEDIR/$APPFOLDER

#Remove old folder from upgrade
sudo rm -rf $SPLUNKAPP/$APPFOLDER/default.old*

#Copy source from splunk install
sudo cp -R  $SPLUNKAPP/$APPFOLDER/ ./$APPFOLDER
sudo rm -rf $APPFOLDER/metadata/local.meta
sudo rm -rf $APPFOLDER/test.xml
sudo chown -R $MYUSER:$MYUSER ./


CURVER=`cat ./$APPFOLDER/default/app.conf | grep -E "version\s=\s" | grep -oE "[0-9]+\.[0-9]+\.[0-9]+"`
MINVER=`echo $CURVER | grep -oE "[0-9]+$"`
STARTVER=`echo $CURVER | grep -oE "^[0-9]+\.[0-9]+"`
SUM=$(($MINVER + 1))
NEWVER="$STARTVER.$SUM"
SEDREG="s/version\s=\s$CURVER/version = $NEWVER/"
TARNAME="$APPFOLDER-$NEWVER.tar.gz"


cd $APPFOLDER/
#Delete all pyc files, not allowed! 
find ./ -type f -name \*.pyc -exec rm -rf "{}" \;

#Delete local folder, not allowed to have in app source
#Paranoid of making a mistake with rm so putting in full path
rm -rf $BASEDIR/$APPFOLDER/local

cd $BASEDIR


echo "Current Version: $CURVER"
echo "New Version: $NEWVER"

sed -i -- "s/version\s=\s$CURVER/version = $NEWVER/" ./$APPFOLDER/default/app.conf
sed -i -- "s/\"version\": \"[0-9]\+\.[0-9]\+\.[0-9]\+\"/\"version\": \"$NEWVER\"/" ./$APPFOLDER/app.manifest 
sed -i -- "s/userAgentVersion = \"[0-9]\+\.[0-9]\+\.[0-9]\+\"/userAgentVersion = \"$NEWVER\"/" ./$APPFOLDER/bin/input_module_SigsciEvent.py
sed -i -- "s/userAgentVersion = \"[0-9]\+\.[0-9]\+\.[0-9]\+\"/userAgentVersion = \"$NEWVER\"/" ./$APPFOLDER/bin/input_module_SigsciRequests.py
sed -i -- "s/^install_source_checksum\s=\s.*$//" ./$APPFOLDER/default/app.conf
rm -rf $TARNAME
tar -czf $TARNAME $APPFOLDER

APPVERSION=`splunk-appinspect list version`
echo "$APPVERSION"
echo "Running Cloud Certification Checks"
splunk-appinspect inspect $TARNAME --mode precert --included-tags cloud > cloud.log
echo "Running All Certification Checks"
splunk-appinspect inspect $TARNAME --mode precert > all_tests.log
