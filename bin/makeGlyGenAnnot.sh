#!/bin/sh
#
#  makeGlyGenAnnot.sh
###########################################################################
#
#  Purpose:
#
#      This script will run the annotation loader for Marker/GlyGen annotations.
#
#  Usage:
#
#      makeGlyGenAnnot.sh
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
#      4) Call makeGlyGenAnnot.py to bucketize the association files.
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
# Establish the log file.
#
LOG=${LOG_DIAG}

#
#
# run annotation loads : delete mode
#

cd ${OUTPUTDIR}

#
# Incremental load of GlyGen domain names as a vocabulary
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Run vocload to load GlyGen domain names (makeGlyGenAnnot.sh)" | tee -a ${LOG}
${VOCLOAD}/runSimpleIncLoadNoArchive.sh ${VOCLOAD}/GlyGen.config 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: Run vocload to load GlyGen domain names (makeGlyGenAnnot.sh)" | tee -a ${LOG}
    exit 1
fi

#
# Call the Python script to create the Marker/GlyGen annotation file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Create the Marker/GlyGen annotation files (makeGlyGenAnnot.sh)" | tee -a ${LOG}
rm -rf ${UNIPROT_GG_ASSOC_FILE}
cp -r ${GLYGEN_FILE} ${UNIPROT_GG_ASSOC_FILE}
${PYTHON} ${UNIPROTLOAD}/bin/makeGlyGenAnnot.py 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: Create the Marker/GlyGen annotation files (makeGlyGenAnnot.sh)" | tee -a ${LOG}
    exit 1
fi

#
#
# run annotation loads
# output files assume the current directory
#

cd ${OUTPUTDIR}

GLYGENCONFIG_CSH=${UNIPROTLOAD}/glygenannot.config
echo "" >> ${LOG}
date >> ${LOG}
echo "Running UniProt Marker/GlyGen annotation load (makeGlyGenAnnot.sh)" >> ${LOG_DIAG}
${ANNOTLOADER_CSH} ${GLYGENCONFIG_CSH}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: Running UniProt Marker/GlyGen annotation load (makeGlyGenAnnot.sh)" | tee -a ${LOG}
    exit 1
fi

exit 0
