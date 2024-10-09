#!/usr/bin/env bash

URN=spiftp.esac.esa.int/data/SPICE/JUICE/kernels/
URI=https://${URN}
DATA_DIR="../data/kernels"
META_KERNEL_NAME="juice_crema_5_1_150lb_23_1_a3.tm"

mkdir -p ${DATA_DIR}

# get data recursively, don't download existing files
wget \
    --recursive \
    --no-parent \
    --continue \
    --no-clobber \
    ${URI} \
    -P ${DATA_DIR}


# WORKAROUND: 
# creating a symlink to shorten the absolute path because 
# spiceypy (or underlying SPICE utils) cuts off the path 
# at >~100 characters.
KERNELS_PATH=$(pwd)/${DATA_DIR}/${URN}
KERNELS_SYM_PATH=$(pwd)/${DATA_DIR}/kernels
if [ ! -L ${KERNELS_SYM_PATH} ]; then
    ln -s ${KERNELS_PATH} ${KERNELS_SYM_PATH}
fi

# as recommended by SPICE:
# set meta kernel's PATH_VALUES and create its backup
META_KERNEL_PATH=${KERNELS_SYM_PATH}/mk/${META_KERNEL_NAME}
PATH_VALUES_OLD="PATH_VALUES       = ( '..' )"
PATH_VALUES="PATH_VALUES       = ( '${KERNELS_SYM_PATH}' )"
sed -i.bak "s|${PATH_VALUES_OLD}|${PATH_VALUES}|" ${META_KERNEL_PATH}