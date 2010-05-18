#!/usr/local/bin/python
#
#  makeUniProtAssocFile.py
###########################################################################
#
#  Purpose:
#
#      This script will use the records in the UniProt input file to create
#      output files that contain:
#
#      1) all of the EntrezGene IDs, Ensembl gene model IDs,
#         EC ids, PDB ids, InterPro ids, SwissProt key words
#         that are associated with each UniProt ID.
#         (all)
#
#      2) all of the UniProt IDs that are SwissProt
#
#      3) all of the UniProt IDs that are TrEMBL
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
#          UNIPROT_ACC1_ASSOC_FILE
#          UNIPROT_ACC2_ASSOC_FILE
#
#  Inputs:
#
#      - Mouse-only UniProt file ($INPUTFILE)
#
#  Outputs:
#
#      - UniProt association file ($UNIPROT_ACC_ASSOC_FILE) to be used by
#        the TableDataSet class. It has the following tab-delimited fields:
#        1) UniProt ID
#        2) EntrezGene IDs (comma-separated)
#        3) Ensembl gene model IDs (comma-separated)
#        4) EC IDs (comma-separated)
#        5) PDB IDs (comma-separated)
#        6) InterPro IDs (comma-separated)
#        7) SPKW Names (comma-separated)
#
#      - SwissProt association file ($UNIPROT_ACC1_ASSOC_FILE) to be used by
#        the TableDataSet class. It has the following tab-delimited fields:
#        1) UniProt ID
#
#      - TrEMBL association file ($UNIPROT_ACC2_ASSOC_FILE) to be used by
#        the TableDataSet class. It has the following tab-delimited fields:
#        1) UniProt ID (TrEMBL)
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
#      4) Write each UniProt ID and its associated ids to the association file.
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
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global uniprotFile, uniprotAccAssocFile, uniprotAcc1AssocFile, uniprotAcc2AssocFile
    global uniprotPDBAssocFile, uniprotECAssocFile, uniprotIPAssocFile, uniprotKWAssocFile
    global fpUniProt, fpAccAssoc, fpAcc1Assoc, fpAcc2Assoc

    uniprotFile = os.getenv('INPUTFILE')
    uniprotAccAssocFile = os.getenv('UNIPROT_ACC_ASSOC_FILE')
    uniprotAcc1AssocFile = os.getenv('UNIPROT_ACC1_ASSOC_FILE')
    uniprotAcc2AssocFile = os.getenv('UNIPROT_ACC2_ASSOC_FILE')

    rc = 0

    #
    # Make sure the environment variables are set.
    #
    if not uniprotFile:
        print 'Environment variable not set: INPUTFILE'
        rc = 1

    if not uniprotAccAssocFile:
        print 'Environment variable not set: UNIPROT_ACC_ASSOC_FILE'
        rc = 1

    if not uniprotAcc1AssocFile:
        print 'Environment variable not set: UNIPROT_ACC1_ASSOC_FILE'
        rc = 1

    if not uniprotAcc2AssocFile:
        print 'Environment variable not set: UNIPROT_ACC2_ASSOC_FILE'
        rc = 1

    #
    # Initialize file pointers.
    #
    fpUniProt = None
    fpAccAssoc = None
    fpAcc1Assoc = None
    fpAcc2Assoc = None

    return rc


#
# Purpose: Open files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global fpUniProt, fpAccAssoc, fpAcc1Assoc, fpAcc2Assoc
    global fpPDBAssoc, fpECAssoc, fpIPAssoc, fpKWAssoc

    #
    # Open the UniProt file.
    #
    try:
        fpUniProt = open(uniprotFile, 'r')
    except:
        print 'Cannot open file: ' + uniprotFile
        return 1

    #
    # Open the acc association file.
    #
    try:
        fpAccAssoc = open(uniprotAccAssocFile, 'w')
    except:
        print 'Cannot open association file: ' + uniprotAccAssocFile
        return 1

    #
    # Open the acc association file.
    #
    try:
        fpAcc1Assoc = open(uniprotAcc1AssocFile, 'w')
    except:
        print 'Cannot open association file: ' + uniprotAcc1AssocFile
        return 1

    #
    # Open the acc association file.
    #
    try:
        fpAcc2Assoc = open(uniprotAcc2AssocFile, 'w')
    except:
        print 'Cannot open association file: ' + uniprotAcc2AssocFile
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

    if fpUniProt:
        fpUniProt.close()

    if fpAccAssoc:
        fpAccAssoc.close()

    if fpAcc1Assoc:
        fpAcc1Assoc.close()

    if fpAcc2Assoc:
        fpAcc2Assoc.close()

    return 0


#
# Purpose: Use a UniProtParser object to get IDs from the UniProt input
#          file and create the association file.
# Returns: 1 if file does not exist or is not readable, else 0
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
        isTrembl = rec.getIsTrembl()
        pdbID = rec.getPDBID()
        ecID = rec.getECID()
        ipID = rec.getInterProID()
        kwName = rec.getKWName()

        #
        # Write the IDs to the association file as long as there is at least
        # one EntrezGene ID or Ensembl ID. If there is more than one
        # EntrezGene ID or Ensembl gene model ID, they are comma-separated
        # within the appropriate field.
        #
        if len(entrezgeneID) > 0 or len(ensemblID) > 0:

	    # all uniprot ids
            fpAccAssoc.write(uniprotID + '\t' + \
                          ','.join(entrezgeneID) + '\t' + \
                          ','.join(ensemblID) + '\t')

	    # EC
	    if len(ecID) > 0:
                fpAccAssoc.write(','.join(ecID))
	    fpAccAssoc.write('\t')

	    # PDB
	    if len(pdbID) > 0:
                fpAccAssoc.write(','.join(pdbID))
	    fpAccAssoc.write('\t')

	    # InterPro
	    if len(ipID) > 0:
                fpAccAssoc.write(','.join(ipID))
	    fpAccAssoc.write('\t')

	    # UniProt/SwissProt key word
	    if len(kwName) > 0:
                fpAccAssoc.write(','.join(kwName))
	    fpAccAssoc.write('\n')

	    # swiss-prot
	    if not isTrembl:
                fpAcc1Assoc.write(uniprotID + '\n')

	    # trembl 
	    else:
                fpAcc2Assoc.write(uniprotID + '\n')

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

