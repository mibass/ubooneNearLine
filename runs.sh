#!/bin/env bash

#check to see if script is already running
if ps ax | grep $0 | grep -v $$ | grep bash | grep -v grep
then
    echo "The script is already running."
    exit 1
fi

source /grid/fermiapp/products/uboone/setup_uboone.sh
setup uboonecode v05_08_00_04 -q e9:prof

cd /uboone/app/home/uboonepro/NearLine
export X509_USER_PROXY=/opt/uboonepro/uboonepro.Production.proxy

./Tracker.py -b
./Analyzer.py 0 -b
./lifetime.gnuplot
./auxplots.gnuplot

./ecl_post.py
rm /tmp/*/MergedLifeTimeHists*.root
