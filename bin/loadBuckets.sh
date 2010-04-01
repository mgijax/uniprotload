#!/bin/sh
#
#  loadBuckets.sh
###########################################################################
#
#  Purpose:
#
#      This script will run the association loader
#      using the MGI/UniProt associations created by the bucketizer.
#
#  Usage:
#
#      loadBuckets.sh
#
#  Env Vars:
#
#      See the configuration file (uniprotload.config)
#
#  Inputs:
#
#      ${MGI_UNIPROT_LOAD_FILE}
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
#      4) Call loadBuckets.py to bucketize the association files.
#
#  Notes:  None
#
###########################################################################

cd `dirname $0`

CONFIG=${UNIPROTLOAD}/uniprotload.config
JOBKEY=$1

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
# Make sure the job key variable was created by the caller
#
if [ ! -f ${JOBKEY} ]
#then
#    echo "Missing job key variable: ${JOBKEY}"
#    exit 1
#fi

#
# Establish the log file.
#
LOG=${LOG_DIAG}

#
#
# run association load
#

echo "Running UniProt association load (loadBuckets.sh)" >> ${LOG}
${ASSOCLOADER_SH} ${CONFIG} ${JOBKEY}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: Running UniProt association load (loadBuckets.sh)" | tee -a ${LOG}
    exit 1
fi

exit 0
