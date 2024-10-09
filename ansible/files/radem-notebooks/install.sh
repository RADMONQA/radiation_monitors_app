#!/usr/bin/env bash

echo "============= INSTALL REQUIREMENTS ============="
python3 -m pip install -r requirements.txt

echo "============= INSTALL CDF UTILS ============="
mkdir -p opt
cd opt
wget https://spdf.gsfc.nasa.gov/pub/software/cdf/dist/cdf39_1/linux/cdf39_1-dist-cdf.tar.gz
tar -xvf cdf39_1-dist-cdf.tar.gz
rm cdf39_1-dist-cdf.tar.gz
cd cdf39_1-dist
make OS=linux ENV=gnu all
cd ../..

echo "============= FETCHING DATA =============" 
./fetch_all.sh

echo "============= RADEM - PROCESSING & UPLOADING =============" 
cd scripts
python3 ./1_processing_raw.py
python3 ./2_processing_csv.py
python3 ./3_processing_line_protocol.py
cd ..

echo ok
