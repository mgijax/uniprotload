#!/usr/local/bin/python
#
#  makeUniProtAssocFile.py
###########################################################################
#
#  Purpose:
#
#      This script will use the records in the UniProt input file to create
#      an output file that contains all of the EntrezGene IDs and Ensembl
#      gene model IDs that are associated with each UniProt ID.
#
#  Usage:
#
#      makeUniProtAssocFile.py
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#          INPUTFILE
#          UNIPROT_ACC_ASSOC_FILE
#
#  Inputs:
#
#      - Mouse-only UniProt file ($INPUTFILE)
#
#  Outputs:
#
#      - UniProt association file ($UNIPROT_ACC_ASSOC_FILE) to be used by
#        the TableDataSet class. It has the following tab-delimited fields:
#
#        1) UniProt ID
#        2) EntrezGene IDs (comma-separated)
#        3) Ensembl gene model IDs (comma-separated)
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
#      3) Create a UniProtParser object to get one UniProt record at a time
#         from the UniProt input file.
#      4) Write each UniProt ID and its associated EntrezGene IDs and
#         Ensembl gene model IDs to the association file.
#      5) Close files.
#
#  Notes:  None
#
###########################################################################

import sys 
import os

import UniProtParser


#
# Purpose: Initialization
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global uniprotFile, uniprotAssocFile
    global fpUniProt, fpAssoc

    uniprotFile = os.getenv('INPUTFILE')
    uniprotAssocFile = os.getenv('UNIPROT_ACC_ASSOC_FILE')

    rc = 0

    #
    # Make sure the environment variables are set.
    #
    if not uniprotFile:
        print 'Environment variable not set: INPUTFILE'
        rc = 1

    if not uniprotAssocFile:
        print 'Environment variable not set: UNIPROT_ACC_ASSOC_FILE'
        rc = 1

    #
    # Initialize file pointers.
    #
    fpUniProt = None
    fpAssoc = None

    return rc


#
# Purpose: Open files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global fpUniProt, fpAssoc

    #
    # Open the UniProt file.
    #
    try:
        fpUniProt = open(uniprotFile, 'r')
    except:
        print 'Cannot open UniProt file: ' + uniprotFile
        return 1

    #
    # Open the association file.
    #
    try:
        fpAssoc = open(uniprotAssocFile, 'w')
    except:
        print 'Cannot open association file: ' + uniprotAssocFile
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
    if fpUniProt:
        fpUniProt.close()
    if fpAssoc:
        fpAssoc.close()

    return 0


#
# Purpose: Use a UniProtParser object to get IDs from the UniProt input
#          file and create the association file.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def getAssociations():

    #
    # Create a UniProtParser object.
    #
    parser = UniProtParser.Parser(fpUniProt)

    #
    # Get the first record from the parser.
    #
    rec = parser.nextRecord()

    #
    # Process each record returned by the parser.
    #
    while rec != None:

        #
        # Get the IDs from the record.
        #
        uniprotID = rec.getUniProtID()
        entrezgeneID = rec.getEntrezGeneID()
        ensemblID = rec.getEnsemblID()

        #
        # Write the IDs to the association file as long as there is at least
        # one EntrezGene ID or Ensembl ID. If there is more than one
        # EntrezGene ID or Ensembl gene model ID, they are comma-separated
        # within the appropriate field.
        #
        if len(entrezgeneID) > 0 or len(ensemblID) > 0:
            fpAssoc.write(uniprotID + '\t' + \
                          ','.join(entrezgeneID) + '\t' + \
                          ','.join(ensemblID) + '\n')

        #
        # Get the next record from the parser.
        #
        rec = parser.nextRecord()

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
