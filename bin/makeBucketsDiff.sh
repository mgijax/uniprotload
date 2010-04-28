#!/bin/sh
#
#  makeBucketsDiff.sh
###########################################################################
#
#  Purpose:
#
#      This script will run the bucket diff-er.
#      That is, the program that generates "diff" files
#      by comparing the old/saved buckets vs. the new/current buckets.
#
#  Usage:
#
#      makeBucketsDiff.sh
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
#      4) Call makeBucketsDiff.py to 
#         compare the old/saved buckets vs. the new/current buckets.
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
# Call the Python script to create the diff files.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Create the diff files (makeBucketsDiff.sh)" | tee -a ${LOG}
./makeBucketsDiff.py 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: Create the diff files (makeBucketsDiff.sh)" | tee -a ${LOG}
    exit 1
fi

exit 0
