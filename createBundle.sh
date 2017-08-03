#!/bin/sh

CURVER=`cat ./sigsci_TA_for_splunk/default/app.conf | grep -E "version\s=\s" | grep -oE "[0-9]+\.[0-9]+\.[0-9]+"`
MINVER=`echo $CURVER | grep -oE "[0-9]+$"`
STARTVER=`echo $CURVER | grep -oE "^[0-9]+\.[0-9]+"`
SUM=$(($MINVER + 1))
NEWVER="$STARTVER.$SUM"
SEDREG="s/version\s=\s$CURVER/version = $NEWVER/"
TARNAME="sigsci_TA_for_splunk-$NEWVER.tar.gz"
APPFOLDER="sigsci_TA_for_splunk"

echo "Current Version: $CURVER"
echo "New Version: $NEWVER"

sed -i -- "s/version\s=\s$CURVER/version = $NEWVER/" ./$APPFOLDER/default/app.conf
sed -i -- "s/\"version\": \"[0-9]\+\.[0-9]\+\.[0-9]\+\"/\"version\": \"$NEWVER\"/" ./$APPFOLDER/app.manifest 
tar -czf $TARNAME $APPFOLDER
