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
#      2:  Non-fatal QC errors detected in the input files
#      3:  Fatal QC errors detected in the input file
#      4:  Warning QC
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

# file with records to load 
inputFileToLoad = os.environ['INPUT_FILE_TOLOAD']

# {mgiID:Association, ...}
markerToUniprotLookup = {}

# {mgiID:Marker, ...}
markerLookup = {}

# lines with missing columns
invalidRowList = []

# input lines mapped to the uniprotId {uniprotId: [lines with that uniprotID, ...}
linesByUniprotDict = {}

# all passing QC (non-fatal, non-skip)
linesToLoadList = []

# lines with invalid MGI IDs (it doesn't exist)
invalidMgiIdList = []

# lines with withdrawn MGI IDs
withdrawnMgiIdList = []

# lines where  MGI ID is non-marker
nonMarkerMgiIdList = []

# add lines where association already exists
addAssocExistsList = []

# delete lines where association doesn't exist
deleteAssocNotExistList = []

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

class Marker:
    # Is: data object for a marker
    # Has: a set of marker attributes
    # Does: provides direct access to its attributes
    #
    def __init__ (self):
        # Purpose: constructor
        # Returns: nothing
        # Assumes: nothing
        # Effects: nothing
        # Throws: nothing
        self.markerID = None
        self.markerPreferred = None
        self.markerStatus = None
        self.organism = None

    def toString(self):
	return '%s, %s, %s, %s' % (self.markerID, self.markerPreferred, self.markerStatus, self.organism)

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
    global markerToUniprotLookup
    global markerLookup 
    openFiles()
   
    # load lookups 
    results = db.sql('''select a1.accid as uniprotID, a1._LogicalDB_key, 
	m.symbol, a2.accid as mgiID
    from ACC_Accession a1, MRK_Marker m, ACC_Accession a2
    where a1. _MGIType_key = 2
    and a1._LogicalDB_key in (13, 41)
    and a1._Object_key = m._Marker_key
    and m._Organism_key = 1
    and m._Marker_Status_key in (1, 3)
    and m._Marker_key = a2._Object_key
    and a2. _MGIType_key = 2
    and a2._LogicalDB_key = 1
    and a2.preferred = 1
    and a2.prefixPart = 'MGI:' ''', 'auto')
 
    for r in results:
	a = Association()
	uniprotID = string.lower(r['uniprotID'])
	a.uniprotID = uniprotID
	mgiID = string.lower(r['mgiID'])
	a.mgiID = mgiID
	a.logicalDbKey = r['_LogicalDB_key']  # swiss-prot or trembl

	if not markerToUniprotLookup.has_key(mgiID):
	    markerToUniprotLookup[mgiID] = []
	markerToUniprotLookup[mgiID].append(a)
    
    # load lookup of all marker MGI IDs
    results = db.sql('''select m.symbol, m._Organism_key, 
	m._Marker_Status_key, a.accid as mgiID, a.preferred
    from ACC_Accession a, MRK_Marker m
    where a. _MGIType_key = 2
    and a._LogicalDB_key = 1
    and a.prefixPart = 'MGI:'
    and a._Object_key = m._Marker_key
    ''', 'auto')
    for r in results:
	m = Marker()
	m.markerID = string.lower(r['mgiID'])
	m.organism = r['_Organism_Key']
	m.markerStatus = r['_Marker_Status_key']
	m.markerPreferred = r['preferred']

	markerLookup[m.markerID] = m

    return

def queryForMgiId(mgiID):
    results = db.sql('''select distinct a._MGIType_key
	from ACC_Accession a
	where a._LogicalDB_key = 1
	and a.accid = "%s"
	and a.prefixPart = 'MGI:' ''' % mgiID, 'auto')

    return results

#
# Purpose: Open input and output files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Sets global variables.
# Throws: Nothing
#
def openFiles ():
    global fpInfile, fpToLoadFile, fpQcRpt

    # curator input file
    try:
        fpInfile = open(inputFile, 'r')
    except:
        print 'Cannot open input file: %s' % inputFile
        sys.exit(1)
    
    # all lines that pass QC
    try:
        fpToLoadFile = open(inputFileToLoad, 'w')
    except:
        print 'Cannot open input file: %s' % inputFileToLoad
        sys.exit(1)

    # QC report file
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

    global hasQcErrors, hasFatalQcErrors, hasWarnings

    lineCt = 0
    hasQcErrors = 0
    hasFatalQcErrors = 0
    hasWarnings = 0

    # throw away header
    header = fpInfile.readline()
    for line in fpInfile.readlines():
	lineCt += 1
	line = string.strip(line)
        tokens = map(string.strip, string.split(line, TAB))
	if len(tokens) < 4:
	    hasFatalQcErrors = 1
	    invalidRowList.append('%s: %s%s' % (lineCt, line, CRT))
	    continue
	# get the uniprot ID and index it to its line for later determination
 	# of duplicate uniprot ID reporting
        uniprotId = string.lower(tokens[0])
	if not linesByUniprotDict.has_key(uniprotId):
	    linesByUniprotDict[uniprotId] = []
	linesByUniprotDict[uniprotId].append('%s: %s%s' % (lineCt, line, CRT))
	    
	mgiID = string.lower(tokens[1])
	ldb = string.lower(tokens[2])
	action = string.lower(tokens[3])

	# check for empty columns
	if uniprotId == '' or mgiID == '' or ldb == '' or action == '':
	    hasFatalQcErrors = 1
            invalidRowList.append('%s: %s%s' % (lineCt, line, CRT))
            continue	
	# check for invalid action value
	if not (action == 'add' or action == 'delete'):
            hasFatalQcErrors = 1
            invalidRowList.append('%s: %s%s' % (lineCt, line, CRT))
	    continue
	# check for invalid logicalDB value
	if not (ldb == 's' or ldb == 't'):
            hasFatalQcErrors = 1
            invalidRowList.append('%s: %s%s' % (lineCt, line, CRT))
            continue

        # check that the MGI ID exists and is for a marker
	qr = queryForMgiId(string.upper(mgiID))
	mgiTypeKeyList = []
	for r in qr:
	    mgiTypeKeyList.append(r['_MGIType_key'])
	if not mgiTypeKeyList:
	    hasQcErrors = 1
            invalidMgiIdList.append('%s: %s%s' % (lineCt, line, CRT))
            continue
	if 2 not in mgiTypeKeyList:
	    hasQcErrors = 1
	    nonMarkerMgiIdList.append('%s: %s%s' %  (lineCt, line, CRT))
	    continue

	# now check that the marker is not withdrawn i.e. markerStatus not
        # interim or official OR mgiID is not preferred
        if markerLookup.has_key(mgiID):
            m = markerLookup[mgiID]
            if m.markerPreferred == 0 or m.markerStatus not in (1, 3):
                hasQcErrors = 1
                withdrawnMgiIdList.append('%s: %s%s' %  (lineCt, line, CRT))
                continue
	
	# check to see if the association exists
	if markerToUniprotLookup.has_key(mgiID):
	    assocList = markerToUniprotLookup[mgiID]
	    assoc = None
	    for a in assocList:
		if a.uniprotID == uniprotId:
		    hasAssoc = 1
		    assoc = a
		    break
	    # report if action is add and association exists
	    if action == 'add' and assoc != None:
		hasQcErrors = 1
		addAssocExistsList.append('%s: %s%s' % (lineCt, line, CRT))    
		continue
	    # report if action is delete and association does not exist
	    if action == 'delete' and assoc == None:
		hasQcErrors = 1
		deleteAssocNotExistList.append('%s: %s%s' % (lineCt, line, CRT))
		continue

	# If we get here, we have a good record, so write it out to the load file
	fpToLoadFile.write('%s%s' % (line, CRT))

    #
    # Report any fatal errors and exit - if found in published file, the load 
    # will not run
    #
    if hasFatalQcErrors:
        if len(invalidRowList):
            fpQcRpt.write('\nInput lines with missing data, invalid action values, invalid logical DB values or < 4 columns:\n')
	    fpQcRpt.write('\nThese errors must be fixed before publishing; if present, the load will not run\n')
            fpQcRpt.write('-----------------------------\n')
            for line in invalidRowList:
                fpQcRpt.write(line)
            fpQcRpt.write('\n')
	    closeFiles()
	    sys.exit(3)

    # 
    # Report any non-fatal errors
    #

    # report dups - if found in the pubished file, the load will load them
    dupList = []
    for id in linesByUniprotDict.keys():
        if len(linesByUniprotDict[id]) > 1:
            dupList = dupList + linesByUniprotDict[id]
	    
    if len(dupList):
	hasWarnings = 1
        fpQcRpt.write('\nUniProt ID listed twice in file. These will be loaded:\n')
	fpQcRpt.write('-----------------------------\n')
	for line in dupList:
	    fpQcRpt.write(line)
	fpQcRpt.write('\n')

    # report other non-fatal errors, the load will not load them
    if hasQcErrors:
	if len(addAssocExistsList):
	    fpQcRpt.write('\nAdd associations that already exist in the database. These will not be loaded:\n')
            fpQcRpt.write('------------------------\n')
            for line in addAssocExistsList:
                fpQcRpt.write(line)
            fpQcRpt.write('\n')
	if len(deleteAssocNotExistList):
            fpQcRpt.write('\nDelete associations that do not exist in the databased:\n')
            fpQcRpt.write('------------------------\n')
            for line in deleteAssocNotExistList:
                fpQcRpt.write(line)
            fpQcRpt.write('\n')
	if len(invalidMgiIdList):
	    fpQcRpt.write('\nInput lines where MGI ID does not exist. These will not be loaded:\n')
            fpQcRpt.write('------------------------\n') 
	    for line in invalidMgiIdList:
                fpQcRpt.write(line)
	    fpQcRpt.write('\n')
	if len(withdrawnMgiIdList):
	    fpQcRpt.write('\nInput lines with withdrawn MGI IDs. These will not be loaded:\n')
            fpQcRpt.write('-------------------------------------------------------------\n')
            for line in withdrawnMgiIdList:
                fpQcRpt.write(line)
	    fpQcRpt.write('\n')
	if len(nonMarkerMgiIdList):
	    fpQcRpt.write('\nInput lines with non-marker MGI ID. These will not be loade:\n')
            fpQcRpt.write('---------------------------------------------------\n')
            for line in nonMarkerMgiIdList:
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
    global fpInfile, fpToLoadFile, fpQcRpt
    fpInfile.close()
    fpToLoadFile.close()
    fpQcRpt.close()
    return

#
# Main
#
checkArgs()
init()
runQcChecks()
closeFiles()
if hasQcErrors or hasWarnings: 
    sys.exit(2)
else:
    sys.exit(0)

