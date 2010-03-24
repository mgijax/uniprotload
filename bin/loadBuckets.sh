#!/bin/sh
#
#  loadBuckets.sh
###########################################################################
#
#  Purpose:
#
#      This script will run the association loader using the MGI/UniProt IDs.
#
#  Usage:
#
#      loadBuckets.sh
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
#      4) Call loadBuckets.py to bucketize the association files.
#
#  Notes:  None
#
###########################################################################

cd `dirname $0`

CONFIG_UNIPROT=${UNIPROTLOAD}/uniprotload.config

#
# Make sure the configuration file exists and source it.
#
if [ -f ${CONFIG_UNIPROT} ]
then
    . ${CONFIG_UNIPROT}
else
    echo "Missing configuration file: ${CONFIG_UNIPROT}"
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
# createArchive including OUTPUTDIR, startLog, getConfigEnv
# sets "JOBKEY"
preload ${OUTPUTDIR}

#
#
# run association load
#

echo "Running UniProt association load" >> ${LOG_DIAG}
echo ${ASSOCLOADER_SH} ${CONFIG_UNIPROT} ${JOBKEY}
${ASSOCLOADER_SH} ${CONFIG_UNIPROT} ${JOBKEY}
STAT=$?
checkStatus ${STAT} "${ASSOCLOADER_SH} ${CONFIG_UNIPROT}"

#
# run postload cleanup and email logs
#
shutDown

#exit 0
