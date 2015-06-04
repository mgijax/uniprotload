#!/bin/sh
#
#  makeBuckets.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the process that bucketizes the
#      MGI/UniProt IDs.
#
#  Usage:
#
#      makeBuckets.sh
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
#      4) Call makeBuckets.py to bucketize the association files.
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
# Make sure the bucket prefix file exists
#
if [ "${BUCKET_PREFIX}" = "" ]
then
    echo "Missing bucket prefix variable: ${BUCKET_PREFIX}"
    exit 1
fi

#
# Establish the log file.
#
LOG=${LOG_DIAG}

#
# Call the Python script to bucketize the association files.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Bucketize the association files (makeBuckets.sh)" | tee -a ${LOG}
./makeBuckets.py ${BUCKET_PREFIX} 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: Bucketize the association files (makeBuckets.sh)" | tee -a ${LOG}
    exit 1
fi

#
# run the post-bucket reports
#

#echo "" >> ${LOG}
#date >> ${LOG}
#echo "Run report (mgi_uniprot.1_0.py)" | tee -a ${LOG}
#./mgi_uniprot.1_0.py 2>> ${LOG}
#STAT=$?
#if [ ${STAT} -ne 0 ]
#then
#    echo "Error: running uniprot report (mgi_uniprot.1_0.py)" | tee -a ${LOG}
#    exit 1
#fi

exit 0
