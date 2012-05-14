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
#      4) all of the UniProt IDs that contain neither EntrezGene nor Ensembl ids (error file)
#	  formats:  all, SwissProt and TrEMBL
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
#          UNIPROT_ACC_ASSOC_ERR_FILE
#          UNIPROT_SP_ASSOC_FILE
#          UNIPROT_SP_ASSOC_ERR_FILE
#          UNIPROT_TR_ASSOC_FILE
#          UNIPROT_TR_ASSOC_ERR_FILE
#
#  Inputs:
#
#      - Mouse-only UniProt file ($INPUTFILE)
#
#  Outputs:
#
#      - UniProt association file ($UNIPROT_ACC_ASSOC_FILE) 
#	 Contains the list of UniProt ids that contain either EntrezGene or Ensembl ids
#      - UniProt association error file ($UNIPROT_ACC_ASSOC_ERR_FILE)
#	 Contains the list of UniProt ids that contain neither EntrezGene nor Ensembl ids
#
#	 It has the following tab-delimited fields:
#        1) UniProt ID
#        2) EntrezGene IDs (comma-separated)
#        3) Ensembl gene model IDs (comma-separated)
#        4) EC IDs (comma-separated)
#        5) PDB IDs (comma-separated)
#        6) InterPro IDs (comma-separated)
#        7) SPKW Names (comma-separated)
#
#      - SwissProt association file ($UNIPROT_SP_ASSOC_FILE) 
#      - SwissProt association file ($UNIPROT_SP_ASSOC_ERR_FILE) 
#	 It has the following tab-delimited fields:
#        1) UniProt ID
#
#      - TrEMBL association file ($UNIPROT_TR_ASSOC_FILE) 
#      - TrEMBL association file ($UNIPROT_TR_ASSOC_ERR_FILE) 
#	 It has the following tab-delimited fields:
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
#  05/09/2012	lec
#	- TR11037/add UniProt association error file ($UNIPROT_ACC_ASSOC_ERR_FILE)
#
###########################################################################

import sys 
import os

import UniProtParser

# INPUTFILE
uniprotFile = None

# UNIPROT_ACC_ASSOC_FILE
uniprotAccAssocFile = None

# UNIPROT_ACC_ASSOC_ERR_FILE
uniprotAccAssocErrFile = None

# UNIPROT_SP_ASSOC_FILE
uniprotSPAssocFile = None

# UNIPROT_SP_ASSOC_ERR_FILE
uniprotSPAssocErrFile = None

# UNIPROT_TR_ASSOC_FILE
uniprotTRAssocFile = None

# UNIPROT_TR_ASSOC_ERR_FILE
uniprotTRAssocErrFile = None

# file pointers
fpUniProt = None
fpAccAssoc = None
fpAccAssocErr = None
fpSPAssoc = None
fpSPAssocErr = None
fpTRAssoc = None
fpTRAssocErr = None

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global uniprotFile, uniprotAccAssocFile, uniprotAccAssocErrFile
    global uniprotSPAssocFile, uniprotSPAssocErrFile
    global uniprotTRAssocFile, uniprotTRAssocErrFile
    global fpUniProt, fpAccAssoc, fpAccAssocErr, fpSPAssoc, fpTRAssoc

    uniprotFile = os.getenv('INPUTFILE')
    uniprotAccAssocFile = os.getenv('UNIPROT_ACC_ASSOC_FILE')
    uniprotAccAssocErrFile = os.getenv('UNIPROT_ACC_ASSOC_ERR_FILE')
    uniprotSPAssocFile = os.getenv('UNIPROT_SP_ASSOC_FILE')
    uniprotSPAssocErrFile = os.getenv('UNIPROT_SP_ASSOC_ERR_FILE')
    uniprotTRAssocFile = os.getenv('UNIPROT_TR_ASSOC_FILE')
    uniprotTRAssocErrFile = os.getenv('UNIPROT_TR_ASSOC_ERR_FILE')

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

    if not uniprotAccAssocErrFile:
        print 'Environment variable not set: UNIPROT_ACC_ASSOC_ERR_FILE'
        rc = 1

    if not uniprotSPAssocFile:
        print 'Environment variable not set: UNIPROT_SP_ASSOC_FILE'
        rc = 1

    if not uniprotSPAssocErrFile:
        print 'Environment variable not set: UNIPROT_SP_ASSOC_ERR_FILE'
        rc = 1

    if not uniprotTRAssocFile:
        print 'Environment variable not set: UNIPROT_TR_ASSOC_FILE'
        rc = 1

    if not uniprotTRAssocErrFile:
        print 'Environment variable not set: UNIPROT_TR_ASSOC_ERR_FILE'
        rc = 1

    #
    # Initialize file pointers.
    #
    fpUniProt = None
    fpAccAssoc = None
    fpAccAssocErr = None
    fpSPAssoc = None
    fpSPAssocErr = None
    fpTRAssoc = None
    fpTRAssocErr = None

    return rc


#
# Purpose: Open files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global fpUniProt, fpAccAssoc, fpAccAssocErr
    global fpSPAssoc, fpSPAssocErr
    global fpTRAssoc, fpTRAssocErr
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
    # Open the acc association error file.
    #
    try:
        fpAccAssocErr = open(uniprotAccAssocErrFile, 'w')
    except:
        print 'Cannot open association error file: ' + uniprotAccAssocErrFile
        return 1

    #
    # Open the acc association file.
    #
    try:
        fpSPAssoc = open(uniprotSPAssocFile, 'w')
    except:
        print 'Cannot open association file: ' + uniprotSPAssocFile
        return 1

    #
    # Open the acc association file.
    #
    try:
        fpSPAssocErr = open(uniprotSPAssocErrFile, 'w')
    except:
        print 'Cannot open association file: ' + uniprotSPAssocErrFile
        return 1

    #
    # Open the acc association file.
    #
    try:
        fpTRAssoc = open(uniprotTRAssocFile, 'w')
    except:
        print 'Cannot open association file: ' + uniprotTRAssocFile
        return 1

    #
    # Open the acc association file.
    #
    try:
        fpTRAssocErr = open(uniprotTRAssocErrFile, 'w')
    except:
        print 'Cannot open association file: ' + uniprotTRAssocErrFile
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

    if fpAccAssocErr:
        fpAccAssocErr.close()

    if fpSPAssoc:
        fpSPAssoc.close()

    if fpSPAssocErr:
        fpSPAssocErr.close()

    if fpTRAssoc:
        fpTRAssoc.close()

    if fpTRAssocErr:
        fpTRAssocErr.close()

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
	uniprotName = rec.getUniProtName()

	#
	# construct the report rows
	# multiple accession ids are comma-separated
	#

	reportRow = ''

	#
	# uniprot ids
	# entrezgene id
	# ensembl id
	#
        reportRow = uniprotID + '\t' + \
                      ','.join(entrezgeneID) + '\t' + \
                      ','.join(ensemblID) + '\t'

	# EC
	if len(ecID) > 0:
            reportRow = reportRow + ','.join(ecID)
	reportRow = reportRow + '\t'

	# PDB
	if len(pdbID) > 0:
            reportRow = reportRow + ','.join(pdbID)
	reportRow = reportRow + '\t'

	# InterPro
	if len(ipID) > 0:
            reportRow = reportRow + ','.join(ipID)
	reportRow = reportRow + '\t'

	# UniProt/SwissProt key word
	if len(kwName) > 0:
            reportRow = reportRow + ','.join(kwName)
	reportRow = reportRow + '\t'

	# UniProt name
	if len(uniprotName) > 0:
            reportRow = reportRow + uniprotName
	reportRow = reportRow + '\n'

	#
	# if exists either EnterzGene id or Ensembl id...
	#
        if len(entrezgeneID) > 0 or len(ensemblID) > 0:

            fpAccAssoc.write(reportRow)

	    # swiss-prot
	    if not isTrembl:
                fpSPAssoc.write(uniprotID + '\n')
    
	    # trembl 
	    else:
                fpTRAssoc.write(uniprotID + '\n')

	#
	# else, write reportRow to error files
	#
        else:
            fpAccAssocErr.write(reportRow)

	    # swiss-prot
	    if not isTrembl:
                fpSPAssocErr.write(reportRow)
    
	    # trembl 
	    else:
                fpTRAssocErr.write(reportRow)

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

