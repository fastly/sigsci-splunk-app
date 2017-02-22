#!/bin/sh


if [ -z $SPLUNK_HOME ]; then
        APPHOME=$HOME/etc/apps/sigsci
else
        APPHOME=$SPLUNK_HOME/etc/apps/sigsci
fi

. $APPHOME/local/config.env

python $APPHOME/bin/sigsci-activity.py
