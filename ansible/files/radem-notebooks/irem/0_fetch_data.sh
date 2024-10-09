#!/usr/bin/env bash

URL=http://srem.psi.ch/datarepo/V0/irem/
DATA_DIR="../data_irem"

mkdir -p ${DATA_DIR}
mkdir -p ${DATA_DIR}/raw
mkdir -p ${DATA_DIR}/extracted
mkdir -p ${DATA_DIR}/csv

# get data recursively, don't download existing files
wget \
    --recursive \
    --no-parent \
    --continue \
    --no-clobber \
    -A gz \
    ${URL} \
    -P ${DATA_DIR}


# remove summary plots dir which we don't care about
rm -rd ../data_irem/srem.psi.ch/datarepo/V0/irem/summaryplots