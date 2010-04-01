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
# Establish the log file.
#
LOG=${LOG_DIAG}
rm -rf ${LOG}
touch ${LOG}

#
# Create the UniProt association file.
#
#echo "" >> ${LOG}
#date >> ${LOG}
#echo "Call makeUniProtAssocFile.sh (uniprotload.sh)" | tee -a ${LOG}
#./makeUniProtAssocFile.sh 2>&1 >> ${LOG}
#STAT=$?
#checkStatus ${STAT} "makeUniProtAssocFile.sh (uniprotload.sh)"

#
# Create the MGI association file.
#
#echo "" >> ${LOG}
#date >> ${LOG}
echo "Call makeMGIAssocFile.sh (uniprotload.sh)" | tee -a ${LOG}
#./makeMGIAssocFile.sh 2>&1 >> ${LOG}
#STAT=$?
#checkStatus ${STAT} "makeMGIAssocFile.sh (uniprotload.sh)"

#
# Bucketized the association files.
#
#echo "" >> ${LOG}
#date >> ${LOG}
#echo "Call makeBuckets.sh (uniprotload.sh)" | tee -a ${LOG}
#./makeBuckets.sh 2>&1 >> ${LOG}
#STAT=$?
#checkStatus ${STAT} "makeBuckets.sh (uniprotload.sh)"

#
# Load association buckets
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call loadBuckets.sh (uniprotload.sh)" | tee -a ${LOG}
./loadBuckets.sh ${JOBKEY} 2>&1 >> ${LOG}
STAT=$?
checkStatus ${STAT} "loadBuckets.sh (uniprotload.sh)"

shutDown
exit 0

#
# Create/load GO annotations
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call makeGOAnnot.sh (uniprotload.sh)" | tee -a ${LOG}
./makeGOAnnot.sh 2>&1 >> ${LOG}
STAT=$?
checkStatus ${STAT} "makeGOAnnot.sh (uniprotload.sh)"

#
# Create/load InterPro annotations
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call makeInterProAnnot.sh (uniprotload.sh)" | tee -a ${LOG}
./makeInterProAnnot.sh 2>&1 >> ${LOG}
STAT=$?
checkStatus ${STAT} "makeInterProAnnot.sh (uniprotload.sh)"

#
# Refresh Inferred-From Cache
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call Inferred From/Accession cache load (uniprotload.sh)" | tee -a ${LOG}
${MGICACHELOAD}/inferredfrom.csh 2>&1 >> ${LOG}
STAT=$?
checkStatus ${STAT} "Inferred From/Accession cache load (uniprotload.sh)"

#
# run postload cleanup and email logs
#
shutDown
exit 0
