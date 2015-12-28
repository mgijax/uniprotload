#!/usr/local/bin/python
#
#  overrideQC.py
###########################################################################
#
#  Purpose:
#
#	This script will generate a QC report for vocabulary 
#	    abbreviation file
#
#  Usage:
#
#      overrideQC.py  filename
#
#      where:
#          filename = path to the input file
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      files that are sourced by the wrapper script:
#
#          QC_RPT
#	   
#  Inputs:
# 	vocabulary abbreviation input file
#	Columns:
#	1. termID
#	2. term
#	3. abbreviation
#
#  Outputs:
#
#      - QC report (${QC_RPT})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  Fatal initialization error occurred
#      2:  QC errors detected in the input files
#
#  Assumes:
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Validate the arguments to the script.
#      2) Perform initialization steps.
#      3) Run the QC checks.
#      5) Close input/output files.
#
#  Notes:  None
#
###########################################################################

import sys
import os
import string
import re
import mgi_utils
import db

#
#  CONSTANTS
#
TAB = '\t'
CRT = '\n'

USAGE = 'Usage: overrideQC.py  inputFile'

#
#  GLOBALS
#

# Report file name
qcRptFile = os.environ['QC_RPT']

# uniprotID:Association, ...}
uniprotToMarkerLookup = {}

# mgiID:Association, ...}
markerToUniprotLookup = {}

# lines with missing columns
invalidRowList = []

# lines with invalid MGI IDs (it doesn't exist)
invalidMgiIDList = []
# lines with withdrawn MGI IDs
withdrawnMgiIdList = []
# lines where  MGI ID is non-marker
nonMarkerMgiIdList = []
# linew where MGI ID is marker, but non-mouse
nonMouseMgiIdList = []

class Association:
    # Is: data object for a uniprot/marker association
    # Has: a set of association attributes
    # Does: provides direct access to its attributes
    #
    def __init__ (self):
        # Purpose: constructor
        # Returns: nothing
        # Assumes: nothing
        # Effects: nothing
        # Throws: nothing
        self.uniprotID = None
	self.markerID = None
        self.logicalDbKey = None
	self.markerPreferred = None
	self.markerStatus = None
	self.organism = None

#
# Purpose: Validate the arguments to the script.
# Returns: Nothing
# Assumes: Nothing
# Effects: sets global variable
# Throws: Nothing
#
def checkArgs ():
    global inputFile

    if len(sys.argv) != 2:
        print USAGE
        sys.exit(1)

    inputFile = sys.argv[1]

    return


#
# Purpose: Perform initialization steps.
# Returns: Nothing
# Assumes: Nothing
# Effects: opens files
# Throws: Nothing
#
def init ():
    global uniprotToMarkerLookup, markerToUniprotLookup
    openFiles()
   
    # load lookups 
    results = db.sql('''select a1.accid as uniprotID, a1._LogicalDB_key, 
	m.symbol, a2.accid as mgiID, a2.preferred, m._Marker_Status_key, 
	m._Organism_key
    from ACC_Accession a1, MRK_Marker m, ACC_Accession a2
    where a1. _MGIType_key = 2
    and a1._LogicalDB_key in (13, 41)
    and a1._Object_key = m._Marker_key
    and m._Marker_key = a2._Object_key
    and a2. _MGIType_key = 2
    and a2._LogicalDB_key = 1
    and a2.prefixPart = 'MGI:' ''', 'auto')
 
    for r in results:
	a = Association()
	uniprotID = r['uniprotID']
	a.uniprotID = uniprotID
	mgiID = r['mgiID']
	a.mgiID = mgiID
	a.logicalDbKey = r['_LogicalDB_key']  # swiss-prot or trembl
	a.mgiPreferred = r['preferred']
	a.status = r['_Marker_Status_key']
	a.organism = r['_Organism_key']

	if not uniprotToMarkerLookup.has_key(uniprotID):
	    uniprotToMarkerLookup[uniprotID] = []
	uniprotToMarkerLookup[uniprotID].append(a)
		
	if not markerToUniprotLookup.has_key(mgiID):
	    markerToUniprotLookup[mgiID] = []
	markerToUniprotLookup[mgiID].append(a)

    return


#
# Purpose: Open input and output files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Sets global variables.
# Throws: Nothing
#
def openFiles ():
    global fpInfile, fpQcRpt

    #
    # Open the input file.
    #
    try:
        fpInfile = open(inputFile, 'r')
    except:
        print 'Cannot open input file: %s' % inputFile
        sys.exit(1)

    try:
        fpQcRpt = open(qcRptFile, 'w')
    except:
        print 'Cannot open report file: %s' % qcRptFile
        sys.exit(1)

    return
#
# Purpose: run the QC checks
# Returns: Nothing
# Assumes: Nothing
# Effects: sets global variables, write report to file system
# Throws: Nothing
#
def runQcChecks ():

    global hasQcErrors, sqlLineList

    lineCt = 0
    hasQcErrors = 0
    for line in fpInfile.readlines():
	lineCt += 1
	line = string.strip(line)
        tokens = string.split(line, TAB)
	print tokens
	print 'len tokens: %s' % len(tokens)
	if len(tokens) < 3:
	    hasQcErrors = 1
	    invalidRowList.append('%s: %s%s' % (lineCt, line, CRT))
	    continue
        uniprotId = tokens[0]
	mgiID = tokens[1]
	ldb = tokens[2]
	action = tokens[3]
	if uniprotId == '' or mgiID == '' or ldb == '' or action == '':
	    hasQcErrors = 1
            invalidRowList.append('%s: %s%s' % (lineCt, line, CRT))
	if action == 'add':# START HERE WHEN IMPLEMENTING QC story
		print 'add'
	elif action == 'delete':
	    	print 'delete'
	else:
	    print 'invalid value for column'
    if hasQcErrors:
	if len(invalidRowList):
	    fpQcRpt.write('\nInput lines with missing data or < 3 columns:\n')
	    fpQcRpt.write('-----------------------------\n')
	    for line in invalidRowList:
		fpQcRpt.write(line)
	    fpQcRpt.write('\n')
	if len(invalidMgiIdList):
	    fpQcRpt.write('\nInput lines with invalid MGI IDs:\n')
            fpQcRpt.write('------------------------\n') 
	    for line in invalidMgiIdList:
                fpQcRpt.write(line)
	    fpQcRpt.write('\n')
	if len(withdrawnMgiIdList):
	    fpQcRpt.write('\nInput lines with withdrawn MGI IDs:\n')
            fpQcRpt.write('-------------------------------------------------------------\n')
            for line in withdrawnMgiIdList:
                fpQcRpt.write(line)
	    fpQcRpt.write('\n')
	if len(nonMarkerMgiIdList):
	    fpQcRpt.write('\nInput lines with non-marker MGI ID :\n')
            fpQcRpt.write('---------------------------------------------------\n')
            for line in nonMarkerMgiIdList:
                fpQcRpt.write(line)
	
	if len(nonMouseMgiIdList):
	    fpQcRpt.write('\nInput lines with non-mouse marker MGI ID :\n')
            fpQcRpt.write('---------------------------------------------------\n')
            for line in nonMouseMgiIdList:
                fpQcRpt.write(line)

    return
	
#
# Purpose: Close the files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def closeFiles ():
    global fpInfile, fpQcRpt
    fpInfile.close()
    fpQcRpt.close()
    return

#
# Main
#
checkArgs()
init()
runQcChecks()
closeFiles()
if hasQcErrors == 1: 
    sys.exit(2)
else:
    sys.exit(0)

