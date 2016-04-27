#!/usr/local/bin/python
#
#  overrideload.py
###########################################################################
#
#  Purpose:
#
#      Delete uniprotload created marker/uniprot relationships or add 
#	relationships that that uniprot does not have
#
#  Usage:
#
#      overrideload.py 
#
#  Inputs:
#
#	Curated override input file
#	1. UniProt ID
#       2. MGI ID
#       3. logical DB
#       4. action
#	5+ Ignored by the load, for curation use 
#
#	2. Configuration - see overrideload.config and override_assocload.config
#
#  Outputs:
#
#       1. assocload ready file
#	2. QC report  
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Validate the arguments to the script.
#      2) Perform initialization steps.
#      3) Open the input/output files.
#      4) Run the QC checks
#      5) Do deletes if no fatal QC errors
#      5) Run the assocload if no fatal QC errors
#      6) Close the input/output files.
#
#  Notes:  None
#
###########################################################################
#
#  Modification History:
#
#  Date        SE   Change Description
#  ----------  ---  -------------------------------------------------------
#
#  01/04/2015  sc  Initial development
#
###########################################################################

import sys
import os
import string
import db
import mgi_utils

db.setAutoTranslate(False)
db.setAutoTranslateBE(False)

#
#  CONSTANTS
#
TAB = '\t'
CRT = '\n'
DATE = mgi_utils.date("%m/%d/%Y")
USAGE='Usage:override.py'

#
#  GLOBALS
#

# input file
inFile = os.environ['INPUT_FILE_TOLOAD']

# output file
assocFile = os.environ['INPUT_FILE_ASSOC']

# file descriptors
fpInFile = ''
fpAssocFile = ''

# logicalDB keys
spLdb= 13
trLdb = 41

# list of associations to write to file
assocList = []

# true if we are about to write the first data line to assocList, i
# if so write header first
firstDataLine = 1

# templates for swissprot and trembl lines
templateSP = '%s\t%s\t\n'
templateTR = '%s\t\t%s\n'

def checkArgs ():
    # Purpose: Validate the arguments to the script.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: exits if unexpected args found on the command line
    # Throws: Nothing

    if len(sys.argv) != 1:
        print USAGE
        sys.exit(1)
    return

# end checkArgs() -------------------------------

def init():
    # Purpose: open file descriptors
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: creates files in the file system, opens db connection

    #
    # Open input and output files
    #
    openFiles()

    #
    # create database connection
    #
    db.useOneConnection(1)


# end init() -------------------------------

def openFiles ():
    # Purpose: Open input/output files.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Sets global variables, exits if a file can't be opened, 
    #  creates files in the file system

    global fpInFile, fpAssocFile

    try:
        fpInFile = open(inFile, 'r')
    except:
        print 'Cannot open override input file: %s' % inFile
        sys.exit(1)

    try:
        fpAssocFile = open(assocFile, 'w')
    except:
        print 'Cannot open override association file: %s' % relationshipFile
        sys.exit(1)


    return

# end openFiles() -------------------------------

def processDelete(uniprotId, mgiId, ldb):
    ldbKey = spLdb
    if ldb == 't':
	ldbKey = trLdb
    print '%s %s' % (mgiId, uniprotId)
    results = db.sql('''select a2._Accession_key
	from ACC_Accession a1, ACC_Accession a2
	where lower(a1.accid) = '%s'
	and a1._LogicalDB_key = 1
	and a1._MGIType_key = 2
	and a1.preferred = 1
	and a1._Object_key = a2._Object_key
	and a2._LogicalDB_key = %s
	and a2. _MGIType_key = 2
	and lower(a2.accid) = '%s' ''' % (mgiId, ldbKey, uniprotId), 'auto')
    print results
    aKey = results[0]['_Accession_key']
    print aKey
    db.sql('''delete from ACC_Accession
	    where _Accession_key = %s''' % aKey, None)
    db.commit()
    return

# end processDelete() -------------------------------

def processAdd(uniprotId, mgiId, ldb):
    global assocList, templateSP, templateTR, firstDataLine

    # add assocload file header
    if firstDataLine == 1:
	fpAssocFile.write('MGI%sSWISS-PROT%sTrEMBL%s' % (TAB, TAB, CRT))
        firstDataLine = 0
    if ldb == 's':
	fpAssocFile.write(templateSP % (string.upper(mgiId), string.upper(uniprotId) ))
    else:
	fpAssocFile.write(templateTR % (string.upper(mgiId), string.upper(uniprotId) ))

    return

# end processAdd() -------------------------------

def closeFiles ():
    # Purpose: Close all file descriptors
    # Returns: Nothing
    # Assumes: all file descriptors were initialized
    # Effects: Nothing
    # Throws: Nothing

    global fpInFile, fpAssocFile

    fpInFile.close()
    fpAssocFile.close()

    return

# end closeFiles() -------------------------------

def process( ): 
    # Purpose: parses override file, creates assocload file
    #  does deletes where indicated
    # Returns: Nothing
    # Assumes: file descriptors have been initialized
    # Effects: writes to the file system
    # Throws: Nothing

    #
    # Iterate throught the input file
    #
    for line in fpInFile.readlines():
	
        tokens = map(string.strip, string.split(line, TAB))
	uniprotId = string.lower(tokens[0])
	mgiId = string.lower(tokens[1])
        ldb = string.lower(tokens[2])
        action = string.lower(tokens[3])
	if action == 'delete':
	    print 'processDelete'
	    processDelete(uniprotId, mgiId, ldb)
	    continue
	print 'processAdd'
	processAdd(uniprotId, mgiId, ldb)

    return

# end process() -------------------------------------


#####################
#
# Main
#
#####################

# check the arguments to this script
print 'checkArgs'
checkArgs()

# this function will exit(1) if errors opening files
print 'init'
init()

# do deletes and create assocload input file
print 'process'
process()

# close all output files
print 'closeFiles'
closeFiles()

db.useOneConnection(0)

sys.exit(0)
