#!/bin/sh
#
#  makeGOAnnot.sh
###########################################################################
#
#  Purpose:
#
#      This script will run the annotation loader for GO/EC associations.
#
#  Usage:
#
#      makeGOAnnot.sh
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
#      4) Call makeGOAnnot.py to bucketize the association files.
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
# createArchive
#
preload

#
#
# make the GO/EC annotation file
#

#
# Call the Python script to create the GO/EC annotation file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Create the GO annotation files (makeGOAnnot.sh)" | tee -a ${LOG}
./makeGOAnnot.py 2>&1 >> ${LOG}
STAT=$?
checkStatus ${STAT} "GO annotation files (makeGOAnnot.sh)"

#
#
# run annotation loads
# output files assume the current directory
#

cd ${OUTPUTDIR}

ECCONFIG_CSH=${UNIPROTLOAD}/goecannot.config
echo "Running UniProt GO/EC annotation load (makeGOAnnot.sh)" >> ${LOG_DIAG}
${ANNOTLOADER_CSH} ${ECCONFIG_CSH}
STAT=$?
checkStatus ${STAT} "UniProt GO/EC annotation load (makeGOAnnot.sh)"

IPCONFIG_CSH=${UNIPROTLOAD}/goipannot.config
echo "Running UniProt GO/InterPro annotation load (makeGOAnnot.sh)" >> ${LOG_DIAG}
${ANNOTLOADER_CSH} ${IPCONFIG_CSH}
STAT=$?
checkStatus ${STAT} "UniProt GO/InterPro annotation load (makeGOAnnot.sh)"

SPKWCONFIG_CSH=${UNIPROTLOAD}/gospkwannot.config
echo "Running UniProt GO/SP-KW annotation load (makeGOAnnot.sh)" >> ${LOG_DIAG}
${ANNOTLOADER_CSH} ${SPKWCONFIG_CSH}
STAT=$?
checkStatus ${STAT} "UniProt GO/SP-KW annotation load (makeGOAnnot.sh)"

#
# run postload cleanup and email logs
#
shutDown
exit 0
