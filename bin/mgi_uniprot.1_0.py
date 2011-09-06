#!/usr/local/bin/python
#
#  mgi_uniprot.1_0.py
###########################################################################
#
#  Purpose:
#
#      This script will select a subset of mgi_uniprot.1_0.txt 
#      where feature type = 'protein coding gene'
#
#  Usage:
#
#      mgi_uniprot.1_0.py
#
#  Inputs:
#
#      - The 1-0 bucket
#
#        ${OUTPUTDIR}/mgi_uniprot.1_0.txt
#
#  Outputs:
#
#      - The 1-0 buckets with 'protein coding gene' only
#
#        ${OUTPUTDIR}/mgi_uniprot.1_0_proteincoding.txt
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Assumes:  Nothing
#
#  Notes:  None
#
#  09/06/2011	lec
#	- TR10834
#
###########################################################################

import sys 
import os
import string
import db

inputFileName = None
outputFileName = None
inputFile = None
outputFile = None

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global inputFileName, outputFileName, inputFile, outputFile

    db.useOneConnection(1)
    db.set_sqlLogFunction(db.sqlLogAll)

    inputFileName = os.getenv('INFILE_1_0')
    outputFileName = os.getenv('OUTPUT_1_0_PROTEINCODING')

    #
    # Make sure the required environment variables are set.
    #
    if not inputFileName:
        print 'Environment variable not set: INFILE_1_0'
        return 1

    #
    # Make sure the required environment variables are set.
    #
    if not outputFileName:
        print 'Environment variable not set: OUTPUT_1_0_PROTEINCODING'
        return 1

    #
    # Open the input file
    #
    try:
        inputFile = open(inputFileName, 'r')
    except:
        print 'Cannot open file: ' + inputFileName
        return 1

    #
    # Open the output file
    #
    try:
        outputFile = open(outputFileName, 'w')
    except:
        print 'Cannot open file: ' + outputFileName
        return 1

    return 0


#
# Purpose: Close files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def closeFiles():

    inputFile.close();
    outputFile.close();

    db.useOneConnection(0)

    return 0


#
# Purpose: Generate file
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def generateReport():

    for line in inputFile.readlines():

        tokens = string.split(line[:-1], '\t')
	id = tokens[0]

	if string.find(id, 'total number') >= 0:
	    continue

	results = db.sql('''
           	select a.accID
           	from ACC_Accession a, VOC_Annot v
		where a._MGIType_key = 2
		and a._LogicalDB_key = 1
		and a.preferred = 1
		and a.accID = "%s"
           	and a._Object_key = v._Object_key
           	and v._AnnotType_key = 1011
           	and v._Term_key = 6238161
		''' % (id), 'auto')

	if len(results) > 0:
	    outputFile.write(line)

    return 0

#
#  MAIN
#

if initialize() != 0:
    sys.exit(1)

if generateReport() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()
sys.exit(0)
