#!/bin/sh

#
# This script is a wrapper around the process that loads 
# Curator Uniprot load overrides
#
#
#     overrideload.sh 
#

USAGE='Usage: overrideload.sh'

#
#  Verify the argument(s) to the shell script.
#
if [ $# -ne 0 ]
then
    echo ${USAGE} | tee -a ${LOG}
    exit 1
fi

cd `dirname $0`/..
CONFIG_LOAD=`pwd`/overrideload.config
CONFIG_ASSOCLOAD=`pwd`/override_assocload.config

cd `dirname $0`
LOG=`pwd`/overrideload.log
rm -rf ${LOG}

#
# verify & source the configuration files
#

if [ ! -r ${CONFIG_LOAD} ]
then
    echo "Cannot read configuration file: ${CONFIG_LOAD}"
    exit 1
fi

. ${CONFIG_LOAD}

#
# Just a verification of where we are at
#

echo "MGD_DBSERVER: ${MGD_DBSERVER}"
echo "MGD_DBNAME: ${MGD_DBNAME}"

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
# verify input file exists and is readable
#

if [ ! -r ${INPUT_FILE_DEFAULT} ]
then
    # set STAT for endJobStream.py
    STAT=1
    checkStatus ${STAT} "Cannot read from input file: ${INPUT_FILE_DEFAULT}"
fi

#####################################
#
# Main
#
#####################################

# remove logs (if not assocload logs will be appended)
cleanDir ${LOGDIR}

#
# createArchive including OUTPUTDIR, startLog, getConfigEnv
# sets "JOBKEY"
#

preload ${INPUTDIR} ${OUTPUTDIR} ${REPORTDIR}

#
# rm all files/dirs from OUTPUTDIR
#

cleanDir ${OUTPUTDIR}

echo "" >> ${LOG_DIAG}
date >> ${LOG_DIAG}
echo "Run QC checks"  | tee -a ${LOG_DIAG}
${UNIPROTLOAD}/bin/overrideQC.sh ${INPUT_FILE_DEFAULT} live
STAT=$?

if [ ${STAT} -eq 1 ]
then
    checkStatus ${STAT} "An error occurred while generating the QC reports - See ${QC_LOGFILE}. overrideQC.sh"

    # run postload cleanup and email logs
    shutDown
fi

if [ ${STAT} -eq 3 ]
then
    checkStatus ${STAT} "Fatal QC errors detected. See ${QC_RPT}. overrideQC.sh"
    
    # run postload cleanup and email logs
    shutDown

fi

#
# run the load
#
echo "" >> ${LOG_DIAG}
date >> ${LOG_DIAG}
echo "Run overrideload.py"  | tee -a ${LOG_DIAG}
${PYTHON} ${UNIPROTLOAD}/bin/overrideload.py  
STAT=$?
checkStatus ${STAT} "UniProt Override Load:"

#
# run the assocload
#

if [ -s "${INPUT_FILE_TOLOAD}" ]
then
    echo "" >> ${LOG_DIAG}
    date >> ${LOG_DIAG}
    echo 'Running UniProt Override Association Load' >> ${LOG_DIAG}
    echo " ${ASSOCLOADER_SH} ${CONFIG_ASSOCLOAD} ${JOBKEY}"
    ${ASSOCLOADER_SH} ${CONFIG_ASSOCLOAD} ${JOBKEY}
    STAT=$?
    checkStatus ${STAT} "${ASSOCLOADER_SH} ${CONFIG_ASSOCLOAD}"
fi

# run postload cleanup and email logs

shutDown

