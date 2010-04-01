#!/bin/sh
#
#  makeSwissProtFile.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the process that creates a report
#      of MGI/UniProt associations in the database that were created by
#      the SwissProt load.
#
#  Usage:
#
#      makeSwissProtFile.sh
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
#      3) Call makeSwissProtRpt.py to create the report.
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
# Call the Python script to create the report of MGI/UniProt associations.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Create MGI/UniProt association report" | tee -a ${LOG}
./makeSwissProtFile.py 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: Create MGI/UniProt association report" | tee -a ${LOG}
    exit 1
fi

exit 0
