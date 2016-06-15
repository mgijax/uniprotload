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
#	1. uniprot ID 
#	2. MGI ID
#	3. logical DB
#	4. action
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

db.setAutoTranslate(False)
db.setAutoTranslateBE(False)

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

# input lines with missing data
missingDataList = []

# input lines with < 3 columns
missingColumnsList = []

# input lines with invalid action values
invalidActionList = []

# input lines with invalid logicalDB values
invalidLdbList = []

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

# lines where no sequence object for uniprot ID
uniprotNotExistsList = []

# lines where sequence object for uniprot ID is non-mouse
uniprotNotMouseList = []

# Counts reported when no fatal errors
loadCt = 0
skipCt = 0

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
    def toString(self):
	return '%s %s %s\n' % (self.uniprotID, self.markerID, self.logicalDbKey) 
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

# end checkArgs() -------------------------------------

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
    # lookup of existing uniprot load associations
    results = db.sql('''select a1.accid as uniprotID, a1._LogicalDB_key, 
	m.symbol, a2.accid as mgiID
    from ACC_Accession a1, MRK_Marker m, ACC_Accession a2
    where a1. _MGIType_key = 2
    and a1._LogicalDB_key in (13, 41)
    and a1._CreatedBy_key = 1442 /*uniprotload_assocload*/
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

# end init() -------------------------------------

def queryForMgiId(mgiID):
    results = db.sql('''select distinct a._MGIType_key
	from ACC_Accession a
	where a._LogicalDB_key = 1
	and a.accid = '%s'
	and a.prefixPart = 'MGI:' ''' % mgiID, 'auto')

    return results

# end queryForMgiId() -------------------------------------
def queryForUniprot(uniprotId):
    results = db.sql( '''select s._Organism_key
        from SEQ_Sequence s, ACC_Accession a
        where a._LogicalDB_key in (13, 41)
        and a._MGIType_key = 19
	and a._Object_key = s._Sequence_key
	and lower(a.accid) = '%s' ''' % uniprotId, 'auto')
    if not len(results):
	return 0
    else:
	return  results[0]['_Organism_key']

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

# end openFiles() -------------------------------------

#
# Purpose: run the QC checks
# Returns: Nothing
# Assumes: Nothing
# Effects: sets global variables, write report to file system
# Throws: Nothing
#
def runQcChecks ():

    global hasQcErrors, hasFatalQcErrors, hasWarnings, loadCt, skipCt

    lineCt = 0
    hasQcErrors = 0
    hasFatalQcErrors = 0
    hasWarnings = 0

    # throw away header
    header = fpInfile.readline()
    for line in fpInfile.readlines():
	print line
	lineCt += 1
	line = string.strip(line)
        tokens = map(string.strip, string.split(line, TAB))
	# skip blank lines
	if  len(tokens) == 1 and tokens[0] == '':
	    continue
	if len(tokens) < 3:
	    hasFatalQcErrors = 1
	    missingColumnsList.append('%s: %s%s' % (lineCt, line, CRT))
	    continue
	# get the uniprot ID and index it to its line for later determination
 	# of duplicate uniprot ID reporting
        uniprotId = string.lower(tokens[0])
	if not linesByUniprotDict.has_key(uniprotId):
	    linesByUniprotDict[uniprotId] = []
	linesByUniprotDict[uniprotId].append('%s: %s%s' % (lineCt, line, CRT))
	    
	mgiID = string.lower(tokens[1])
	action = string.lower(tokens[2])

	# check for empty columns
	if uniprotId == '' or mgiID == '' or action == '':
	    hasFatalQcErrors = 1
            missingDataList.append('%s: %s%s' % (lineCt, line, CRT))
            continue	
	# check for invalid action value
	if not (action == 'add' or action == 'delete'):
            hasFatalQcErrors = 1
            invalidActionList.append('%s: %s%s' % (lineCt, line, CRT))
	    continue

        # check that the MGI ID exists and is for a marker
	qr = queryForMgiId(string.upper(mgiID))
	mgiTypeKeyList = []
	for r in qr:
	    mgiTypeKeyList.append(r['_MGIType_key'])
	if not mgiTypeKeyList:
	    hasQcErrors = 1
	    skipCt += 1
            invalidMgiIdList.append('%s: %s%s' % (lineCt, line, CRT))
            continue
	if 2 not in mgiTypeKeyList:
	    hasQcErrors = 1
	    skipCt += 1
	    nonMarkerMgiIdList.append('%s: %s%s' %  (lineCt, line, CRT))
	    continue

	# now check that the marker is not withdrawn i.e. markerStatus not
        # interim or official OR mgiID is not preferred
        if markerLookup.has_key(mgiID):
            m = markerLookup[mgiID]
            if m.markerPreferred == 0 or m.markerStatus not in (1, 3):
                hasQcErrors = 1
	 	skipCt += 1
                withdrawnMgiIdList.append('%s: %s%s' %  (lineCt, line, CRT))
                continue
	# check to see if there is a uniprot sequence in the database
	# and it is a mouse
	organismKey = queryForUniprot(uniprotId)
	print 'organismKey = queryForUniprot(uniprotId): %s' % organismKey
	if organismKey == 0:
	    hasQcErrors = 1
	    skipCt += 1
	    uniprotNotExistsList.append('%s: %s%s' %  (lineCt, line, CRT))
	    continue
	if organismKey != 1:
	    hasQcErrors = 1
            skipCt += 1
	    uniprotNotMouseList.append('%s: %s%s' %  (lineCt, line, CRT))
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
		skipCt += 1
		addAssocExistsList.append('%s: %s%s' % (lineCt, line, CRT))    
		continue
	    # report if action is delete and association does not exist
	    if action == 'delete' and assoc == None:
		hasQcErrors = 1
		skipCt += 1
		deleteAssocNotExistList.append('%s: %s%s' % (lineCt, line, CRT))
		continue
	else: # this marker has no uniprot associations
	    if action == 'delete':
		hasQcErrors = 1
                skipCt += 1
                deleteAssocNotExistList.append('%s: %s%s' % (lineCt, line, CRT))
		continue
	# If we get here, we have a good record, write it out to the load file
	loadCt +=1
	fpToLoadFile.write('%s%s' % (line, CRT))

    #
    # Report any fatal errors and exit - if found in published file, the load 
    # will not run
    #

    if hasFatalQcErrors:
	fpQcRpt.write('\nThese errors must be fixed before publishing; if present, the load will not run\n\n')

        if len(missingColumnsList):
            fpQcRpt.write('\nInput lines with < 3 columns:\n')
            fpQcRpt.write('-----------------------------\n')
            for line in missingColumnsList:
                fpQcRpt.write(line)
            fpQcRpt.write('\n')

        if len(missingDataList):
            fpQcRpt.write('\nInput lines with missing data:\n')
            fpQcRpt.write('-----------------------------\n')
            for line in missingDataList:
                fpQcRpt.write(line)
            fpQcRpt.write('\n')

        if len(invalidActionList):
            fpQcRpt.write('\nInput lines with invalid Action value. Must be one of (a, A, d, D). :\n')
            fpQcRpt.write('-----------------------------\n')
            for line in invalidActionList:
                fpQcRpt.write(line)
            fpQcRpt.write('\n')

        if len(invalidLdbList):
            fpQcRpt.write('\nInput lines with invalid Trembl or Swiss-Prot value. Must be one of (t, T, s, S). :\n')
            fpQcRpt.write('-----------------------------\n')
            for line in invalidLdbList:
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
        fpQcRpt.write('\nUniProt ID listed twice in file. These will be processed if they pass all QC:\n')
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
            fpQcRpt.write('\nDelete associations that do not exist in the database. These will not be processed:\n')
            fpQcRpt.write('------------------------\n')
            for line in deleteAssocNotExistList:
                fpQcRpt.write(line)
            fpQcRpt.write('\n')
	if len(invalidMgiIdList):
	    fpQcRpt.write('\nInput lines where MGI ID does not exist. These will not be processed:\n')
            fpQcRpt.write('------------------------\n') 
	    for line in invalidMgiIdList:
                fpQcRpt.write(line)
	    fpQcRpt.write('\n')
	if len(withdrawnMgiIdList):
	    fpQcRpt.write('\nInput lines with withdrawn MGI IDs. These will not be processed:\n')
            fpQcRpt.write('-------------------------------------------------------------\n')
            for line in withdrawnMgiIdList:
                fpQcRpt.write(line)
	    fpQcRpt.write('\n')
	if len(nonMarkerMgiIdList):
	    fpQcRpt.write('\nInput lines with non-marker MGI ID. These will not be processed:\n')
            fpQcRpt.write('---------------------------------------------------\n')
            for line in nonMarkerMgiIdList:
                fpQcRpt.write(line)
	    fpQcRpt.write('\n')
	if len(uniprotNotExistsList):
	    fpQcRpt.write('\nInput lines where UniProt Sequence does not exist in the database. These will not be processed:\n')
	    fpQcRpt.write('---------------------------------------------------\n')
	    for line in uniprotNotExistsList:
		 fpQcRpt.write(line)
	    fpQcRpt.write('\n')
	if len(uniprotNotMouseList):
            fpQcRpt.write('\nInput lines where UniProt Sequence is not mouse. These will not be processed:\n')
            fpQcRpt.write('---------------------------------------------------\n')
            for line in uniprotNotMouseList:
                 fpQcRpt.write(line)

	print '%sNumber with non-fatal QC errors, these will not be processed: %s' % (CRT, skipCt)
	print 'Number with no QC errors, these will be loaded: %s%s' % ( loadCt, CRT)
    return

# end runQcChecks() -------------------------------------
	
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

# end closeFiles() -------------------------------------

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

