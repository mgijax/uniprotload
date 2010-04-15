#!/bin/sh

cd `dirname $0`

CONFIG=uniprotload.config

if [ -f ../${CONFIG} ]
then
    . ../${CONFIG}
else
    echo "Missing configuration file: ${CONFIG}"
    exit 1
fi

if [ ! -f ${MGI_UNIPROT_LOAD_FILE} ]
then
    echo "Missing input file: ${MGI_UNIPROT_LOAD_FILE}"
    exit 1
fi

if [ ! -f ${MGI_UNIPROT_OLDLOAD} ]
then
    echo "Missing input file: ${MGI_UNIPROT_OLDLOAD}"
    exit 1
fi

./compare.py

exit 0
