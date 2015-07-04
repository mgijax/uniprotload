#!/usr/local/bin/python
#
#  makeMGIAssocFile.py
###########################################################################
#
#  Purpose:
#
#      This script will create an output file that contains all of the
#      EntrezGene IDs, Ensembl gene model IDs, EMBL IDs that are associated with
#      MGI markers.
#
#  Usage:
#
#      makeMGIAssocFile.py
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#          MGI_ACC_ASSOC_FILE
#
#  Inputs:  None
#
#  Outputs:
#
#      - MGI association file ($MGI_ACC_ASSOC_FILE) to be used by the
#        TableDataSet class. It has the following tab-delimited fields:
#
#        1) MGI ID (for a marker)
#        2) Symbol
#	 3) Marker Types
#        4) EntrezGene IDs (comma-separated)
#        5) Ensembl gene model IDs (comma-separated)
#        6) EMBL IDs (comma-separated)
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Assumes:  Nothing
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Initialize variables.
#      2) Open files.
#      3) Query the database to get a list of MGI markers and the
#         EntrezGene IDs and Ensembl gene model IDs that are associated
#         with those markers.
#      4) Write each MGI ID and its associated IDs to the association file.
#      5) Close files.
#
#  Notes:  None
#
# 05/26/2010    lec
#       - TR 10231/output should contain marker type 'gene' only
#	  marker type field added
#
###########################################################################

import sys 
import os
import db

# file name MGI_ACC_ASSOC_FILE
mgiAssocFile = None

# file pointer
fpAssoc = None

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global mgiAssocFile
    global fpAssoc

    mgiAssocFile = os.getenv('MGI_ACC_ASSOC_FILE')

    rc = 0

    #
    # Make sure the environment variables are set.
    #
    if not mgiAssocFile:
        print 'Environment variable not set: MGI_ACC_ASSOC_FILE'
        rc = 1

    #
    # Initialize file pointers.
    #
    fpAssoc = None

    return rc


#
# Purpose: Open files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global fpAssoc

    #
    # Open the association file.
    #
    try:
        fpAssoc = open(mgiAssocFile, 'w')
    except:
        print 'Cannot open association file: ' + mgiAssocFile
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

    if fpAssoc:
        fpAssoc.close()

    db.useOneConnection(0)

    return 0


#
# Purpose: Query the database to get associations to MGI markers and
#          create the association file.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def getAssociations():

    #
    # Get all of the EntrezGene IDs, Ensembl gene model IDs, EMBL sequences
    # that are associated with markers and load them into a temp table.
    #
    # marker must also have status official or interum
    #
    db.sql('''select a1.accID, a1._Object_key, a1._LogicalDB_key, a2.accID as mgiID, m.symbol, m._Marker_Type_key
              INTO TEMP TABLE assoc 
              from ACC_Accession a1, ACC_Accession a2, MRK_Marker m 
              where a1._MGIType_key = 2 and 
                 a1._LogicalDB_key in (9, 55, 60) and 
                 a1.preferred = 1 and 
                 a1._Object_key = m._Marker_key and 
                 m._Organism_key = 1 and 
                 a1._Object_key = a2._Object_key and 
                 a2._MGIType_key = 2 and 
                 a2._LogicalDB_Key = 1 and 
                 a2.preferred = 1 and
                 a2.prefixPart = 'MGI:'
		''', None)

    #
    # Add indexes to the temp table.
    #
    db.sql('create nonclustered index idx_accID on assoc (accID)', None)
    db.sql('create nonclustered index idx_object on assoc (_Object_key)', None)
    db.sql('create nonclustered index idx_logicalDB on assoc (_LogicalDB_key)', None)

    #
    # Get the MGI ID of the marker and the unique EntrezGene IDs
    # that are associated with each marker.
    #
    cmd = '''select distinct mgiID, accID 
             from assoc 
             where _LogicalDB_key = 55 
             order by mgiID'''
    results = db.sql(cmd, 'auto')

    #
    # Create a dictionary lookup where the key is the MGI ID and the value
    # is a list of associated EntrezGene IDs.
    #
    entrezgeneDict = {}
    for r in results:
        mgiID = r['mgiID']
        accID = r['accID']
        if not entrezgeneDict.has_key(mgiID):
            entrezgeneDict[mgiID] = []
        entrezgeneDict[mgiID].append(accID)

    #
    # Get the MGI ID of the marker and the unique Ensembl gene model IDs
    # that are associated with each marker.
    #
    cmd = '''select distinct mgiID, accID 
             from assoc 
             where _LogicalDB_key = 60 
             order by mgiID'''
    results = db.sql(cmd, 'auto')

    #
    # Create a dictionary lookup where the key is the MGI ID and the value
    # is a list of association Ensembl gene model IDs.
    #
    ensemblDict = {}
    for r in results:
        mgiID = r['mgiID']
        accID = r['accID']
        if not ensemblDict.has_key(mgiID):
            ensemblDict[mgiID] = []
        ensemblDict[mgiID].append(accID)

    #
    # Get the MGI ID of the marker and the unique EMBL IDs
    # that are associated with each marker.
    #
    # EMBL IDs associated with at most one marker
    #
    cmd = '''select distinct mgiID, accID
             from assoc
             where _LogicalDB_key = 9
	     group by accID having count(*) = 1
             order by mgiID'''
    results = db.sql(cmd, 'auto')

    #
    # Create a dictionary lookup where the key is the MGI ID and the value
    # is a list of association EMBL gene IDs.
    #
    emblDict = {}
    for r in results:
        mgiID = r['mgiID']
        accID = r['accID']
        if not emblDict.has_key(mgiID):
            emblDict[mgiID] = []
        emblDict[mgiID].append(accID)

    #
    # Get a unique list of all MGI IDs from the temp table.
    #
    cmd = '''select distinct mgiID, symbol, _Marker_Type_key
             from assoc 
             order by mgiID'''
    results = db.sql(cmd, 'auto')

    #
    # For each MGI ID, get the associated IDs from the dictionaries and
    # write them to the association file.
    #
    for r in results:

        mgiID = r['mgiID']
        symbol = r['symbol']
        markerType = r['_Marker_Type_key']

        if entrezgeneDict.has_key(mgiID):
            entrezgeneID = entrezgeneDict[mgiID]
        else:
            entrezgeneID = []

        if ensemblDict.has_key(mgiID):
            ensemblID = ensemblDict[mgiID]
        else:
            ensemblID = []

        if emblDict.has_key(mgiID):
            emblID = emblDict[mgiID]
        else:
            emblID = []

        #
        # Write the IDs to the association file. If there is more than one
        # EntrezGene ID or Ensembl ID, they are comma-separated within the
        # appropriate field.
        #
        fpAssoc.write(mgiID + '\t' + \
		      symbol + '\t' + \
		      str(markerType) + '\t' + \
                      ','.join(entrezgeneID) + '\t' + \
                      ','.join(ensemblID) + '\t' + \
                      ','.join(emblID) + '\n')

    return 0


#
#  MAIN
#

db.useOneConnection(1)

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if getAssociations() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()
sys.exit(0)
