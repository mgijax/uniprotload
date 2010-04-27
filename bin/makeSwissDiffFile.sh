#!/bin/sh
#
#  makeSwissDiffFile.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the process that creates a report
#      of MGI/SwissProt associations in the database
#      and compares it to new MGI/UniProt bucketizer files.
#
#  Usage:
#
#      makeSwissDiffFile.sh
#
#  Env Vars:
#
#      See the configuration file (uniprotload.config)
#
#  Inputs:
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
#      3) Call makeUniProtOldFile.py to create the file on existing UniProt associations.
#      4) Call makeSwissDiffFile.py to create the comparisons (run the bucketizer).
#
#  Notes:  None
#
###########################################################################

cd `dirname $0`

CONFIG=uniprotload.config
BUCKETPREFIX=$1

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
# Call the Python script to create the report of MGI/SwissProt associations.
# Then, compare the differences between SwissProt and new MGI/UniProt buckets.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Create MGI/SwissProt association report & compare the differences" | tee -a ${LOG}
./makeSwissDiffFile.py 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: Create MGI/SwissProt association report & compare the differences" | tee -a ${LOG}
    exit 1
fi

exit 0
