#!/bin/sh
#
#  postUniProt.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the process that runs the post uniprot updates
#
#  Usage:
#
#      postUniProt.sh
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
#      4) Call postUniProt.py
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
# grep the GCRP info from the 10090 fasta file
# this is to find the single GCRP ids
#
echo "" >> ${LOG}
date >> ${LOG}
echo "grep the GCRP info from the 10090 fasta file (postUniProt.sh)" | tee -a ${LOG}
rm -rf ${GCRP_IDS_TXT} | tee -a ${LOG}
gunzip -c ${GCRP_FILE} | grep "^>" | cut -d "|" -f 2 > ${GCRP_IDS_TXT} | tee -a ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: grep the GCRP info from the 10090 fasta file (postUniProt.sh)" | tee -a ${LOG}
    exit 1
fi

#
# Call the Python script to execute the post uniprot updates
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Process Post UniProt updates (postUniProt.sh)" | tee -a ${LOG}
${PYTHON} ./postUniProt.py 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: Process Post UniProt updates (postUniProt.sh)" | tee -a ${LOG}
    exit 1
fi

exit 0
