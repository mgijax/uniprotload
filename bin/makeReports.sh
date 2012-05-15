#!/bin/sh
#
#  makeReports.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the process that creates the UniProt
#      association file.
#
#  Usage:
#
#      makeReports.sh
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
#      2) Verify that the input file exists.
#      3) Establish the log file.
#      4) Call makeReports.py to create the association file.
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
# Call the Python script to create the UniProt association file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Create the UniProt/MGI report file (makeReports.sh)" | tee -a ${LOG}
./makeReports.py 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: Create the UniProt/MGI report file (makeReports.sh)" | tee -a ${LOG}
    exit 1
fi

exit 0
