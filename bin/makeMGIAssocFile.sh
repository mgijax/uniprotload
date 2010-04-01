#!/bin/sh
#
#  makeMGIAssocFile.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the process that creates the MGI
#      association file.
#
#  Usage:
#
#      makeMGIAssocFile.sh
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
#      3) Call makeMGIAssocFile.py to create the association file.
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
# Call the Python script to create the MGI association file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Create the MGI association file (makeMGIAssocFile.sh)" | tee -a ${LOG}
./makeMGIAssocFile.py 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error creating MGI association file" | tee -a ${LOG}
    exit 1
fi
date >> ${LOG}

exit 0
