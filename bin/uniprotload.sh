#!/bin/sh
#
#  uniprotload.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the entire UniProt load process.
#
#  Usage:
#
#      uniprotload.sh
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
#      2) Establish the log file.
#      4) Call makeUniProtAssocFile.sh to make an association file
#         from the UniProt input file.
#      5) Call makeMGIAssocFile.sh to make an association file from
#         the database.
#      6) Call makeBuckets.sh to bucketize the association files.
#      7) Call loadBuckets.sh to load associations created by bucketizer.
#
#  Notes:  None
#
###########################################################################

cd `dirname $0`

CONFIG=uniprotload.config

#
# Make sure the configuration file exists and source it.
#
if [ -f ../${CONFIG} ]
then
    . ../${CONFIG}
else
    echo "Missing configuration file: ${CONFIG}"
    exit 1
fi

#
# Establish the log file.
#
LOG=${LOG_DIAG}

#
# Create the UniProt association file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call makeUniProtAssocFile.sh (uniprotload.sh)" | tee -a ${LOG}
./makeUniProtAssocFile.sh 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    exit 1
fi

#
# Create the MGI association file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call makeMGIAssocFile.sh (uniprotload.sh)" | tee -a ${LOG}
./makeMGIAssocFile.sh 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    exit 1
fi

#
# Bucketized the association files.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call makeBuckets.sh (uniprotload.sh)" | tee -a ${LOG}
./makeBuckets.sh 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    exit 1
fi

#
# Load association buckets
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call oadBuckets.sh (uniprotload.sh)" | tee -a ${LOG}
./loadBuckets.sh 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    exit 1
fi

exit 0
