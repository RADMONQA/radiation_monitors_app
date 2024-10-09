#!/usr/bin/env bash

echo "============= FETCHING RADEM =============" 
cd processing
./0_fetching_ftp.sh
cd ..

# echo "============= FETCHING IREM =============" 
# cd irem
# ./0_fetch_data.sh
# cd ..

echo "============= FETCHING KERNELS =============" 
cd kernel
./0_fetch_data.sh
cd ..

echo ok