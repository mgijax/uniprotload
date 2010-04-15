#!/usr/local/bin/python
#
#  makeUniProtOldFile.py
###########################################################################
#
#  Purpose:
#
#      This script will create an output file that contains all of the
#      MGI/UniProt associations in the database.
#
#  Usage:
#
#      makeUniProtOldFile.py
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#          MGI_UNIPROT_OLDLOAD
#
#  Inputs:  None
#
#  Outputs:
#
#      - MGI/UniProt association file from the database with
#        the following tab-delimited fields:
#
#        1) MGI ID (for a marker)
#        2) UniProt ID
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
#      3) Create a file of MGI/UniProt associations in the database	
#      4) Close files.
#
#  Notes:  None
#
###########################################################################

import sys 
import os
import db


#
# Purpose: Initialization
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global oldAssocFile, fpOldAssoc

    oldAssocFile = os.getenv('MGI_UNIPROT_OLDLOAD')

    rc = 0

    #
    # Make sure the required environment variables are set.
    #
    if not oldAssocFile:
        print 'Environment variable not set: MGI_UNIPROT_OLDLOAD'
        rc = 1

    #
    # Initialize file pointers.
    #
    fpOldAssoc = None

    return rc


#
# Purpose: Open files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global fpOldAssoc

    #
    # Open the report files.
    #
    try:
        fpOldAssoc = open(oldAssocFile, 'w')
    except:
        print 'Cannot open report: ' + oldAssocFile
        return 1

    return 0


#
# Purpose: Close files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def closeFiles():
    if fpOldAssoc:
        fpOldAssoc.close()

    return 0


#
# Purpose: Create a file of the MGI/UniProt associations in the database
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def getAssociations():
    #
    # Get all the MGI/UniProt association 
    #
    results = db.sql('select a1.accID "mgiID", a2.accID "uniprotID" ' + \
                     'from ACC_Accession a1, ACC_Accession a2 ' + \
                     'where a1._MGIType_key = 2 and ' + \
                           'a1._LogicalDB_key = 1 and ' + \
                           'a1.prefixPart = "MGI:" and ' + \
                           'a1.preferred = 1 and ' + \
                           'a1._Object_key = a2._Object_key and ' + \
                           'a2._MGIType_key = 2 and ' + \
                           'a2._LogicalDB_key in (13,41) and ' + \
                           'a2._CreatedBy_key = 1442 ' + \
                     'order by a1.accID, a2.accID', 'auto')

    #
    # Write the MGI/UniProt associations to the file.
    #
    for r in results:
        mgiID = r['mgiID']
        uniprotID = r['uniprotID']
        fpOldAssoc.write(mgiID + '\t' + uniprotID + '\n')

    return 0


#
#  MAIN
#

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if getAssociations() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()
sys.exit(0)
