#!/bin/sh
#
#  makeECAnnot.sh
###########################################################################
#
#  Purpose:
#
#      This script will run the annotation loader for GO/EC associations.
#
#  Usage:
#
#      makeECAnnot.sh
#
#  Env Vars:
#
#      See the configuration file (uniprotload.config)
#
#  Inputs:  None
#
#  Outputs:
#
#      - Log file (${LOG_DIAG})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  Fatal error occurred
#
#  Assumes:  Nothing
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Source the configuration file to establish the environment.
#      2) Verify that the input files exist.
#      3) Establish the log file.
#      4) Call makeECAnnot.py to bucketize the association files.
#
#  Notes:  None
#
###########################################################################

cd `dirname $0`

CONFIG=${UNIPROTLOAD}/uniprotload.config

#
# Make sure the configuration file exists and source it.
#
if [ -f ${CONFIG} ]
then
    . ${CONFIG}
else
    echo "Missing configuration file: ${CONFIG}"
    exit 1
fi

#
# Make sure the MGI association load file exists.
#
if [ ! -f ${MGI_UNIPROT_LOAD_FILE} ]
then
    echo "Missing input file: ${MGI_UNIPROT_LOAD_FILE}"
    exit 1
fi

#
# Establish the log file.
#
LOG=${LOG_DIAG}

#
#  Source the DLA library functions.
#

if [ "${DLAJOBSTREAMFUNC}" != "" ]
then
    if [ -r ${DLAJOBSTREAMFUNC} ]
    then
        . ${DLAJOBSTREAMFUNC}
    else
        echo "Cannot source DLA functions script: ${DLAJOBSTREAMFUNC}" | tee -a ${LOG}
        exit 1
    fi
else
    echo "Environment variable DLAJOBSTREAMFUNC has not been defined." | tee -a ${LOG}
    exit 1
fi

#
# createArchive
#
#preload

#
#
# make the GO/EC annotation file
#

#
# Call the Python script to create the GO/EC annotation file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Create the Go/EC annotation file (makeECAnnot.sh)" | tee -a ${LOG}
./makeECAnnot.py 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error creating GO/EC annotation file" | tee -a ${LOG}
    exit 1
fi

#
#
# run annotation load
#

#CONFIG_CSH=${UNIPROTLOAD}/ecannot.config

#echo "Running UniProt/EC annotation load (makeECAnnot.sh)" >> ${LOG_DIAG}
#${ANNOTLOADER_CSH} ${CONFIG_CSH}
#STAT=$?
#checkStatus ${STAT} "${ANNOTLOADER_CSH} ${CONFIG_CSH}"

#
# run postload cleanup and email logs
#
#shutDown
exit 0
