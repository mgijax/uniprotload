#!/usr/local/bin/python
#
#  makeReports.py
###########################################################################
#
#  Purpose:
#
#  Usage:
#
#      makeReports.py
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#          MGI_ACC_ASSOC_FILE
#          UNIPROT_SP_ASSOC_ERR_FILE
#	   UNIPROT_SP_ASSOC_MGI_FILE
#
#  Inputs:
#
#      - MGI association file ($MGI_ACC_ASSOC_FILE)
#        to be used by the TableDataSet class. 
#        It has the following tab-delimited fields:
#
#        1) MGI ID (for a marker)
#        2) Marker Symbol
#        3) Marker Type
#        4) EntrezGene IDs and NBCI gene model IDs (comma-separated)
#        5) Ensembl gene model IDs (comma-separated)
#
#      - UniProt SwissProt association that have neither EntrezGene nor Ensembl ids
#		($UNIPROT__SP_ASSOC_ERR_FILE)
#        It has the following tab-delimited fields:
#        1) UniProt ID
#        2) UniProt Name
#
#  Outputs:
#
#	 UniProt/MGI associations ($UNIPROT_SP_ASSOC_MGI_FILE)
#	 1) UniProt ID (field 1 (err file))
#	 2) UniProt Name (field  2 (err file))
#	 3) MGI ID (field 1)
#	 4) EntrezGene IDs (field 4)
#	 5) Ensembl IDs (field 5)
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
# 05/14/2012    lec
#       - TR11071/report for sending to UniProt
#
###########################################################################

import sys 
import os
import string
import db

# MGI_ACC_ASSOC_FILE
mgiAssocFile = None

# UNIPROT_SP_ASSOC_ERR_FILE
uniprotSPAssocErrFile = None

# UNIPROT_SP_ASSOC_MGI_FILE
reportFile = None

# reads MGI_ACC_ASSOC_FILE
mgiLookup = {}

# file pointers
fpMGIAssoc = None
fpSPAssoc = None
fp = None

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global mgiAssocFile, uniprotSPAssocErrFile, reportFile
    global fpMGIAssoc, fpSPAssoc, fp

    mgiAssocFile = os.getenv('MGI_ACC_ASSOC_FILE')
    uniprotSPAssocErrFile = os.getenv('UNIPROT_SP_ASSOC_ERR_FILE')
    reportFile = os.getenv('UNIPROT_SP_ASSOC_MGI_FILE')

    rc = 0

    #
    # Make sure the required environment variables are set.
    #
    if not mgiAssocFile:
        print 'Environment variable not set: MGI_ACC_ASSOC_FILE'
        rc = 1

    if not uniprotSPAssocErrFile:
        print 'Environment variable not set: UNIPROT_SP_ASSOC_ERR_FILE'
        rc = 1

    if not reportFile:
        print 'Environment variable not set: UNIPROT_SP_ASSOC_MGI_FILE'
        rc = 1

    fpMGIAssoc = None
    fpSPAssoc = None
    fp = None

    return rc


#
# Purpose: Open files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global mgiLookup
    global fpMGIAssoc, fpSPAssoc, fp

    #
    # Open the MGI association file.
    #
    try:
        fpMGIAssoc = open(mgiAssocFile, 'r')
    except:
        print 'Cannot open MGI association file: ' + uniprotSPAssocErrFile
        return 1

    #
    # Open the swissprot association file.
    #
    try:
        fpSPAssoc = open(uniprotSPAssocErrFile, 'r')
    except:
        print 'Cannot open swissprot association file: ' + uniprotSPAssocErrFile
        return 1

    #
    # Open the report file.
    #
    try:
        fp = open(reportFile, 'w')
    except:
        print 'Cannot open report file: ' + reportFile
        return 1

    #
    # put MGI association file into mgiLookup
    #
    for line in fpMGIAssoc.readlines():
        tokens = string.split(line[:-1], '\t')
        key = tokens[1]
        value = tokens
        mgiLookup[key] = []
        mgiLookup[key].append(value)

    return 0

#
# Purpose: Close files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def closeFiles():

    if fpMGIAssoc:
        fpMGIAssoc.close()

    if fpSPAssoc:
        fpSPAssoc.close()

    if fp:
        fp.close()

    return 0

#
# Purpose: Write report(s)
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def writeReport():

    #
    # for each SP association err found...
    #

    for line in fpSPAssoc.readlines():
	tokens = string.split(line[:-1], '\t')

	uniprotID = tokens[0]
	name = tokens[1]

	if name == '[]':
	    continue

	fp.write(uniprotID + '\t')
	fp.write(name + '\t')

	#
	# find info from MGI (MGI id, EntrezGene id, Ensembl id)
	#
	if mgiLookup.has_key(name):
	    fp.write(mgiLookup[name][0][0] + '\t')
	    fp.write(mgiLookup[name][0][3] + '\t')
	    fp.write(mgiLookup[name][0][4] + '\n')
	else:
	    fp.write('\t\t\n')

    return 0

#
#  MAIN
#

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if writeReport() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()
sys.exit(0)
