#!/bin/sh


if [ -z $SPLUNK_HOME ]; then
        APPHOME=$HOME/etc/apps/sigsci_TA_for_splunk
else
        APPHOME=$SPLUNK_HOME/etc/apps/sigsci_TA_for_splunk
fi

. $APPHOME/local/config.env

python $APPHOME/bin/sigsci-activity.py
